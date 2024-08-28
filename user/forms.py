from django.contrib.auth.forms import PasswordChangeForm, UserChangeForm

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class PasswordValidation:

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields didn't match.")
        return password2


class SignUpForm(UserCreationForm, PasswordValidation):
    email = forms.EmailField(max_length=254,
                             help_text='Required. I'
                                       'nform a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("A user with that username already exists.")
        return username


class EditProfileForm(UserChangeForm):
    password1 = forms.CharField(widget=forms.PasswordInput(),
                                required=False, label="New password")
    password2 = forms.CharField(widget=forms.PasswordInput(),
                                required=False,
                                label="New password confirmation")

    class Meta:
        model = User
        fields = ('username',)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exclude(
                pk=self.instance.pk).exists():
            raise ValidationError("A user with that username already exists.")
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 or password2:
            if password1 != password2:
                raise ValidationError("The two password fields didn't match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        password1 = self.cleaned_data.get('password1')
        if password1:
            user.set_password(password1)

        if commit:
            user.save()
        return user


class CustomPasswordChangeForm(PasswordChangeForm, PasswordValidation):
    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2')