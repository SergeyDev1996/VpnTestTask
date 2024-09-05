from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.urls import reverse_lazy

from .forms import SignUpForm, EditProfileForm
from django.contrib.auth.decorators import login_required


@login_required  # Ensure only logged-in users can access this view
def user_profile(request):
    user = request.user
    context = {
        'email': user.email,
        'username': user.username
    }
    return render(request, 'user/user_profile.html', context)


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('sites:my_sites')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return HttpResponseRedirect(reverse_lazy("user:profile"))
    else:
        form = SignUpForm()
    return render(request, 'user/signup_template.html', {'form': form})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return HttpResponseRedirect(reverse_lazy("user:profile"))
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'user/edit_profile.html', {'form': form})
