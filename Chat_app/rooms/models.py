from django.db import models
from django.contrib.auth.models import User

# Database Model of a Chat room
class Room(models.Model):
    name = models.CharField(max_length=225)
    slug = models.SlugField(unique=True)
    is_private = models.BooleanField(default=False)
    
    # Participants for private room
    participants = models.ManyToManyField(User, blank=True)
    
    def __str__(self):
        return self.name

# Database Model of Chat messages    
class ChatMessage(models.Model):
    
    MESSAGE_TYPE = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File')
    )
    
    room = models.ForeignKey(Room, related_name='message', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='user', on_delete=models.CASCADE)
    content = models.TextField(max_length=300, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    
    # Field for file support
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE, default='text')
    
    class Meta:
        ordering = ('date_added',)
        
    def __str__(self):
        return f"Message created by {self.user.username} in {self.room.name} Group"
