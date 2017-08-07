from django import forms
from django.core.validators import RegexValidator
import bleach
import markdown
from django.utils.html import escape
import re
from .models import Post, UserProfile, Comment
from django.forms import ModelForm
from django.conf import settings

class RegisterForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100, validators=[RegexValidator(r'^[a-zA-Z0-9-_]+$', "Only letters, digits, hyphen and underscore without spaces are allowed")])
    password = forms.CharField(label='Password', max_length=100, widget=forms.PasswordInput)
    email = forms.EmailField()

class ProfileForm(forms.Form):
    email = forms.EmailField()
    about = forms.CharField(max_length=1000, widget=forms.Textarea)

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

class AdminCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment_text', 'comment_text_html', 'post', 'parent', 'user', 'deleted', 'upvotes', 'downvotes', 'net_votes']

    def clean(self):
        if self.cleaned_data['parent']:
            if self.cleaned_data['parent'].post != self.cleaned_data['post']:
                raise forms.ValidationError("The parent comment chosen does not belong to the selected post.")
        comment_text = self.cleaned_data['comment_text']

        comment_text_html = markdown.markdown(comment_text)
        comment_text_html = bleach.clean(comment_text_html, tags=settings.COMMENT_TAGS, strip=True)

        self.cleaned_data['comment_text_html'] = comment_text_html

        return self.cleaned_data

class PostModelForm(ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 10}),
        }

class AdminUserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['user', 'about']
        widgets = {
            'about': forms.Textarea(attrs={'rows': 10}),
        }

class CommentForm(forms.Form):
    comment = forms.CharField(label='Comment', max_length=2000, widget=forms.Textarea)