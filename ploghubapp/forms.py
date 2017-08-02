from django import forms
from django.core.validators import RegexValidator
import bleach
import markdown
from django.utils.html import escape
import re
from .models import Post
from django.forms import ModelForm
from django.conf import settings

class RegisterForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100, validators=[RegexValidator(r'^[a-zA-Z0-9-_]+$', "Only letters, digits, hyphen and underscore without spaces are allowed")])
    password = forms.CharField(label='Password', max_length=100, widget=forms.PasswordInput)
    email = forms.EmailField()

class ProfileForm(forms.Form):
    email = forms.EmailField()

class AdminPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title','body', 'body_html', 'user', 'deleted', 'upvotes', 'downvotes', 'net_votes', 'rank']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 10}),
        }

    def clean(self):
        body = self.cleaned_data['body']

        body_html = markdown.markdown(body)
        body_html = bleach.clean(body_html, tags=settings.ARTICLE_TAGS, strip=True)

        self.cleaned_data['body_html'] = body_html

        return self.cleaned_data

class PostModelForm(ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 10}),
        }