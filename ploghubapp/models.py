from django.db import models
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import datetime
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey

class Post(models.Model):
    """
    Represents a link to an external learning resource
    """

    #Fields
    title = models.CharField(max_length=150)
    body = models.CharField(max_length=20000)
    body_html = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    deleted = models.BooleanField(default=False)
    upvotes = models.IntegerField(default=1)
    downvotes = models.IntegerField(default=0)
    net_votes = models.IntegerField(default=1)
    rank = models.FloatField(default=0.0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):

        return self.title

    def calculate_rank(self):
        now = timezone.now()
        timediff = now - self.created
        minutes = int(timediff.total_seconds()/60)
        hours = int(minutes/60)
        rank = (self.net_votes - 1)/pow(hours+2,1.5)
        self.rank = rank
        self.save()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    about = models.CharField(max_length=1000)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

class Comment(MPTTModel):
    """
    Represents a comment
    """
    #Fields
    comment_text = models.TextField()
    comment_text_html = models.TextField()
    deleted = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    net_votes = models.IntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['net_votes']
    
    def __str__(self):
        return self.comment_text

    def time_since_posted(self):
        now = timezone.now()
        timediff = now - self.created
        minutes = int(timediff.total_seconds()/60)
        hours = int(minutes/60)
        days = int(hours/24)
        if minutes < 60:
            if minutes == 1:
                return "{} minute ago".format(minutes)
            else:    
                return "{} minutes ago".format(minutes)
        if hours < 24:
            if hours == 1:
                return "{} hour ago".format(hours)
            else:
                return "{} hours ago".format(hours)
        if days == 1:
            return "{} day ago".format(days)
        else:
            return "{} days ago".format(days)