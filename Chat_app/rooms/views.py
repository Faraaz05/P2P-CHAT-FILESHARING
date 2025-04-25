from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Room, ChatMessage
from .forms import RoomForm

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
    room = get_object_or_404(Room,slug=slug)
    messages = ChatMessage.objects.filter(room=room)[0:25]   
    
    return render(request, 'rooms/chat.html', {
        "room":room,
        "messages":messages,
        })
    
