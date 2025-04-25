from django.contrib import admin

# Register your models here.

from .models import Room, ChatMessage

admin.site.register(Room)
admin.site.register(ChatMessage)


