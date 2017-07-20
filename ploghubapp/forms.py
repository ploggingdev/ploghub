from django import forms
from django.core.validators import RegexValidator
import bleach
import markdown
from django.utils.html import escape
import re

class RegisterForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100, validators=[RegexValidator(r'^[a-zA-Z0-9-_]+$', "Only letters, digits, hyphen and underscore without spaces are allowed")])
    password = forms.CharField(label='Password', max_length=100, widget=forms.PasswordInput)
    email = forms.EmailField()

class ProfileForm(forms.Form):
    email = forms.EmailField()