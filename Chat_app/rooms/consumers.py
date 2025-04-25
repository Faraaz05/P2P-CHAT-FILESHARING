import json
import base64
import uuid

from channels.generic.websocket import AsyncWebsocketConsumer   # Class for creating consumer
from channels.db import database_sync_to_async  # For storing things into database in asynchronous view
from asgiref.sync import async_to_sync
from django.core.files.base import ContentFile

from django.contrib.auth.models import User
from .models import Room, ChatMessage


class ChatConsumer(AsyncWebsocketConsumer):
    # Creating connection
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        
        # # Get the room check if it's private
        # room = await self.get_room()
        
        # # Check room privacy
        # if room.is_private:
        #     # For private rooms, check user's participation
        #     is_participant = await self.check_room_participation(room)
        #     if not is_participant:
        #         await self.close()
        #         return 
        
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
         
        room = await self.get_room(roomslug)
        user, picture = await self.get_user(username)
        
        # Create and Save message
        if room:
            message_obj = await self.save_message(
                room=room,
                user=user,
                content=message_content,
                message_type=message_type,
                file=file_data if has_file else None
            )
            
        # response data for message group
        response_data = {
            'type': 'chat_message',
            'username': username,
            'message': message_content,
            'picture': picture.url,
            'message_type': message_type,
        }
        
        if has_file:
            response_data['file_url'] = message_obj.file.url 
            response_data['filename'] = message_obj.file.name.split('/')[-1] 
            
        # Send response data to message group
        await self.channel_layer.group_send(
            self.room_group_name,
            response_data
        )
       
    async def chat_message(self, event):
        # Send data to websocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'message_type': event['message_type'],
            'picture': event.get('picture'),
            'file_url': event.get('file_url'),
            'filename': event.get('filename')
        }))
        
    @database_sync_to_async
    def get_room(self, roomslug):
        return Room.objects.get(slug=roomslug)
    
    @database_sync_to_async
    def get_user(self, username):
        user = User.objects.get(username=username)
        return user, user.profile.picture
    
    # @database_sync_to_async
    # def check_room_participation(self, room):
    #     user = self.scope['user']
    #     return room.participants.filter(id=user.id).exists()   
    
    
    # Store data in database     
    @database_sync_to_async
    def save_message(self, user, room, content, message_type, file=None):
        message_obj = ChatMessage.objects.create(
            user=user,
            room=room,
            content=content,
            message_type=message_type
        )

        if file:
            # If file is base64 encoded data
            if isinstance(file, str) and file.startswith('data:'):
                format_info, base64_str = file.split(';base64,')
                content_type = format_info.split(':')[-1]
                file_ext = content_type.split('/')[-1]
                
                # Generate unique file name
                unique_id = uuid.uuid4().hex[:8]
                file_name = f"{user.username}_{unique_id}.{file_ext}"
                
                # Decode and save file
                try:
                    decoded_file = base64.b64decode(base64_str)
                    message_obj.file.save(file_name, ContentFile(decoded_file), save=True)
                except Exception as e:
                    print(f"Error saving the file: {e}")
            
            # If file is already a file object
            elif hasattr(file, 'name'):
                message_obj.file = file
                message_obj.save()
                
        return message_obj
        