from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from django.contrib.auth.models import User
from .models import Profile


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
        widgets = {
            "username": forms.TextInput(attrs={
                "placeholder": "Enter your Username",
                "class": "form-control"
            })
        }
    
    # The password fields are defined on the form class itself, not on the model.
    # So override them to set widget attributes  
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
            
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            "placeholder": "Enter your Password",
            "class": "form-control"
        })
            
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            "placeholder": "Confirm Password",
            "class": "form-control"
        })
        
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username','first_name','last_name','email']
        widgets = {
            "username": forms.TextInput(attrs={
                "class": "form-control"
            }),
            "first_name": forms.TextInput(attrs={
                "class": "form-control"
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control"
            })
        }
        
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['birth_date', 'picture']
        widgets = {
            "birth_date": forms.DateInput(attrs={
            "class": "form-control",
            "type": "date"
            }),
            "picture": forms.FileInput(attrs={
            "class": "form-control"
            })
        }
      
class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Enter your Username",
        "class": "form-control"
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        "placeholder": "Enter your Password",
        "class": "form-control"
    }))
        