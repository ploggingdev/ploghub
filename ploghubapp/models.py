from django.db import models
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import datetime
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify

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