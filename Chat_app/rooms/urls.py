from django.urls import path
from .views import chatgroup, chat

# Media + static routes and urls import
from django.conf import settings
from django.conf.urls.static import static

app_name = 'rooms'

urlpatterns = [
    path('', chatgroup, name='chatgroup'),
    path('<slug:slug>/', chat, name='chat')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)