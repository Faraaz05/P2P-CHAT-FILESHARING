from django.shortcuts import render, redirect

from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.db import transaction

from .forms import SignUpForm, UserUpdateForm, ProfileUpdateForm

# Homepage View
def index(request):
    return render(request, 'core/index.html')

# Sign Up View
def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            user.set_password(form.cleaned_data.get('password1'))
            user = authenticate(username=user.username, password=form.cleaned_data.get('password1'))
            user.save()
            
            login(request, user)
            return redirect('core:index')
    else:
        form = SignUpForm()
        
    return render(request, 'core/signup.html', {"form": form})


# Profile Update View
@login_required
@transaction.atomic         # Send signal to database whenever profile is update
def update_profile(request):
    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('core:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    return render(request, 'core/update_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })
    
    
# Profile View   
@login_required
def profile(request):  
    return render(request, 'core/profile.html')