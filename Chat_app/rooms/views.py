from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Room, ChatMessage
from .forms import RoomForm
import logging
import os

logger = logging.getLogger(__name__)

# Try to import the translation utility, fall back if it fails
try:
    from utils.translation import translate_text
except ImportError:
    logger.warning("Translation module not found or not working. Using fallback.")
    # Fallback function if translation module is not available
    def translate_text(text, target_language, source_language=None):
        return text  # Just return the original text

@login_required
def chatgroup(request):
    chatgroups = Room.objects.all()
    
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            
    else:
        form = RoomForm()
        
    return render(request, 'rooms/chatgroup.html', {
        "chatgroups": chatgroups,
        "form": form
        })

@login_required
def chat(request, slug):
    room = get_object_or_404(Room, slug=slug)
    # Get the 25 most recent messages, ordered by date
    messages = ChatMessage.objects.filter(room=room).order_by('-date_added')[:25]

    # Reverse the order to display oldest first (chronological order for chat)
    messages = list(messages)  # Convert QuerySet to list for reversing
    messages.reverse()
    
    # Get user's preferred language
    user_language = request.user.profile.preferred_language
    
    # Translate messages if needed (for initial load)
    translated_messages = []
    for msg in messages:
        # Process file messages to extract filename
        if msg.file:
            # Extract filename from file path
            msg.filename = os.path.basename(msg.file.name)
        
        # Only translate text messages, not files/images
        if msg.message_type == 'text' and msg.source_language != user_language:
            try:
                translated_content = translate_text(msg.content, user_language, msg.source_language)
                msg.translated_content = translated_content
                msg.is_translated = True
            except Exception as e:
                logger.error(f"Translation error: {e}")
                msg.translated_content = msg.content
                msg.is_translated = False
        else:
            msg.translated_content = msg.content
            msg.is_translated = False
        
        translated_messages.append(msg)
    return render(request, 'rooms/chat.html', {
        "room": room,
        "messages": translated_messages,
        })