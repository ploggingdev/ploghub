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
    body = models.CharField(max_length=1000)
    body_html = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    deleted = models.BooleanField(default=False)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    net_votes = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()