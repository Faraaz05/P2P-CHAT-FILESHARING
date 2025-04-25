from django.urls import path
from .views import index, signup, update_profile, profile

# Build-in views import for login and logout 
from django.contrib.auth import views
from .forms import LoginForm

# Media + static routes and urls import
from django.conf import settings
from django.conf.urls.static import static

app_name = 'core'

urlpatterns = [
    path('', index, name='index'),
    path('signup/', signup, name='signup'),
    path('login/', views.LoginView.as_view(template_name='core/login.html', authentication_form=LoginForm), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', profile, name='profile'),
    path('update_profile', update_profile, name='update_profile')
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
