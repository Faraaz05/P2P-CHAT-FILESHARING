from django.db import models
from django.contrib.auth.models import User

# Django's build-in signals for model operations
from django.db.models.signals import post_save
from django.dispatch import receiver

# Pillow image re-sizing import
from PIL import Image

class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    birth_date = models.DateField(blank=True, null=True)
    picture = models.ImageField(default='profile_pics/default_pic.png', upload_to='profile_pics/', blank=True) 
    
    # Add language preference field with popular Indian languages
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('gu', 'Gujarati'),
        ('bn', 'Bengali'),
        ('ta', 'Tamil'),
        ('te', 'Telugu'),
        ('mr', 'Marathi'),
        ('kn', 'Kannada'),
        ('ml', 'Malayalam'),
        ('pa', 'Punjabi'),
        ('or', 'Odia'),
        ('ur', 'Urdu'),
        ('as', 'Assamese'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('zh-cn', 'Chinese'),
        ('ja', 'Japanese'),
        ('ru', 'Russian'),
    ]
    
    preferred_language = models.CharField(
        max_length=10, 
        choices=LANGUAGE_CHOICES,
        default='en',
        verbose_name="Preferred Language"
    )
    
    def __str__(self):
        return self.user.username
    
    # Re-sizing profile picture to 400 X 400 pixels if not already
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.picture and hasattr(self.picture, 'path') and self.picture.path:
            pic = Image.open(self.picture.path)
            if pic.height > 400 or pic.width > 400:
                output_size = (400, 400)
                pic.thumbnail(output_size)
                pic.save(self.picture.path)
            
            
# Signals to create/save profile when User is created/updated
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()