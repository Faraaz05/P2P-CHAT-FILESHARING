import json
import base64
import uuid
import logging
import os

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.files.base import ContentFile

from django.contrib.auth.models import User
from .models import Room, ChatMessage

logger = logging.getLogger(__name__)

# Try to import the translation utility, fall back if it fails
try:
    from utils.translation import translate_text
except ImportError:
    logger.warning("Translation module not found or not working. Using fallback.")
    # Fallback function if translation module is not available
    def translate_text(text, target_language, source_language=None):
        return text  # Just return the original text

class ChatConsumer(AsyncWebsocketConsumer):
    # Creating connection
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        
        # Join Chat Group with provided room detail
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Authenticate and accept user/consumer
        await self.accept()
        
    # Creating disconnect function in asynchronous view
    async def disconnect(self, close_code):
        # Leave Chat Group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
    # Method to get user's preferred language
    @database_sync_to_async
    def get_user_preferred_language(self, username):
        try:
            user = User.objects.get(username=username)
            return user.profile.preferred_language
        except Exception as e:
            logger.error(f"Error getting user language preference: {e}")
            return 'en'  # Default to English if there's an error
        
    # Receive text messages or file data and store it
    async def receive(self, text_data):
        # Handling incoming message from websocket
        data = json.loads(text_data)
        
        username = data['username']
        message_content = data.get('message', '')
        roomslug = data['roomslug']
        message_type = data.get('message_type', 'text')
        has_file = data.get('has_file', False)
        file_data = data.get('file', None)
        filename = data.get('filename', None)  # Get filename if provided
        
        # Get user's language preference
        source_language = await self.get_user_preferred_language(username)
         
        room = await self.get_room(roomslug)
        user, picture = await self.get_user(username)
        
        # Create and Save message with original content and source language
        if room:
            message_obj = await self.save_message(
                room=room,
                user=user,
                content=message_content,
                message_type=message_type,
                file=file_data if has_file else None,
                source_language=source_language,
                filename=filename  # Pass filename to save_message
            )
            
        # response data for message group
        response_data = {
            'type': 'chat_message',
            'username': username,
            'message': message_content,
            'picture': picture.url,
            'message_type': message_type,
            'original_language': source_language,  # Include original language
        }
        
        if has_file and message_obj.file:
            response_data['file_url'] = message_obj.file.url 
            # Use original filename if available, otherwise extract from path
            response_data['filename'] = filename or os.path.basename(message_obj.file.name)
            
        # Send response data to message group
        await self.channel_layer.group_send(
            self.room_group_name,
            response_data
        )
       
    # Modify chat_message to translate message before sending to client
    async def chat_message(self, event):
        try:
            # Get current user's preferred language
            current_user = self.scope['user'].username
            target_language = await self.get_user_preferred_language(current_user)
            
            # Translate message if needed and it's a text message
            message = event['message']
            original_language = event.get('original_language', 'en')
            
            translated_message = message
            need_translation = (
                event['message_type'] == 'text' and 
                target_language != original_language and
                message.strip()  # Only translate non-empty messages
            )
            
            if need_translation:
                try:
                    translated_message = await self.translate_message(
                        message, 
                        target_language,
                        original_language
                    )
                except Exception as e:
                    logger.error(f"Translation failed: {e}")
                    translated_message = message  # Fallback to original
            
            # Extract filename for file messages
            filename = event.get('filename')
            if event.get('file_url') and not filename:
                filename = os.path.basename(event.get('file_url', ''))
            
            # Send data to websocket
            await self.send(text_data=json.dumps({
                'message': translated_message,
                'original_message': message,  # Include original for toggle option
                'username': event['username'],
                'message_type': event['message_type'],
                'picture': event.get('picture'),
                'file_url': event.get('file_url'),
                'filename': filename,
                'translated': need_translation and translated_message != message,
                'source_language': original_language,
                'target_language': target_language
            }))
        except Exception as e:
            logger.error(f"Error in chat_message: {e}")
            # Send a simplified version if there's an error
            await self.send(text_data=json.dumps({
                'message': event['message'],
                'username': event['username'],
                'message_type': event['message_type'],
                'picture': event.get('picture'),
                'file_url': event.get('file_url'),
                'filename': event.get('filename'),
            }))
    
    # Add method to translate message asynchronously
    @database_sync_to_async
    def translate_message(self, text, target_language, source_language=None):
        try:
            return translate_text(text, target_language, source_language)
        except Exception as e:
            logger.error(f"Translation error in consumer: {e}")
            return text  # Return original text on error
        
    @database_sync_to_async
    def get_room(self, roomslug):
        return Room.objects.get(slug=roomslug)
    
    @database_sync_to_async
    def get_user(self, username):
        user = User.objects.get(username=username)
        return user, user.profile.picture
    
    # Update save_message to include source language and handle filename
    @database_sync_to_async
    def save_message(self, user, room, content, message_type, file=None, source_language='en', filename=None):
        message_obj = ChatMessage.objects.create(
            user=user,
            room=room,
            content=content,
            message_type=message_type,
            source_language=source_language
        )

        if file:
            # If file is base64 encoded data
            if isinstance(file, str) and file.startswith('data:'):
                format_info, base64_str = file.split(';base64,')
                content_type = format_info.split(':')[-1]
                file_ext = content_type.split('/')[-1]
                
                # Use original filename if provided, otherwise generate one
                if filename:
                    # Make sure we keep the extension matching the content type
                    name_parts = os.path.splitext(filename)
                    base_name = name_parts[0]
                    file_name = f"{base_name}_{uuid.uuid4().hex[:6]}.{file_ext}"
                else:
                    # Generate unique file name
                    unique_id = uuid.uuid4().hex[:8]
                    file_name = f"{user.username}_{unique_id}.{file_ext}"
                
                # Decode and save file
                try:
                    decoded_file = base64.b64decode(base64_str)
                    message_obj.file.save(file_name, ContentFile(decoded_file), save=True)
                except Exception as e:
                    logger.error(f"Error saving the file: {e}")
            
            # If file is already a file object
            elif hasattr(file, 'name'):
                message_obj.file = file
                message_obj.save()
                
        return message_obj