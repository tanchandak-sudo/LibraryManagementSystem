from django import forms
from django.contrib.auth.models import User
from .models import Profile

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username','password','email','first_name','last_name']
        widgets = {"password": forms.PasswordInput(),}

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["role"]

class StudentRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ["first_name", "email", "username", "password"]