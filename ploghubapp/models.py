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
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    net_votes = models.IntegerField(default=0)
    rank = models.FloatField(default=0.0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):

        return self.title

    def calculate_rank(self, comments_count):
        now = timezone.now()
        timediff = now - self.created
        minutes = int(timediff.total_seconds()/60)
        hours = int(minutes/60)

        comment_weight = 0.2
        gravity = 1.5
        amplifier = 100000

        rank = (self.net_votes +(comments_count*comment_weight) - 1)/pow(hours+2,gravity)*amplifier
        self.rank = rank
        self.save()

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
    
    def get_post_url(self):
        slug = slugify(self.title)
        return reverse('ploghubapp:view_post', args=[self.id, self.user, slug])
    
    def can_delete(self):
        if self.deleted:
            return False
        now = timezone.now()
        timediff = now - self.created
        minutes = int(timediff.total_seconds()/60)
        hours = int(minutes/60)
        if hours <= 23 and Comment.objects.filter(post=self).filter(deleted=False).count() == 0:
            return True
        else:
            return False
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    about = models.CharField(max_length=1000, default="[empty]")
    comment_karma = models.IntegerField(default=0)
    submission_karma = models.IntegerField(default=0)
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
    net_votes = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['-net_votes']
    
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
    
    def can_delete(self):
        if self.deleted:
            return False
        now = timezone.now()
        timediff = now - self.created
        minutes = int(timediff.total_seconds()/60)
        hours = int(minutes/60)
        if hours <= 1 and Comment.objects.filter(parent=self).filter(deleted=False).count() == 0:
            return True
        else:
            return False
    
    def can_edit(self):
        if self.deleted:
            return False
        now = timezone.now()
        timediff = now - self.created
        minutes = int(timediff.total_seconds()/60)
        hours = int(minutes/60)
        if hours <= 1:
            return True
        else:
            return False
    
    def get_post_url(self):
        slug = slugify(self.post.title)
        return reverse('ploghubapp:view_post', args=[self.post.id, self.post.user, slug])

class VoteComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    value = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def change_vote(self, new_vote_value, request_user):
        if self.value == -1 and new_vote_value == 1:  # down to up
            vote_diff = 2
            self.comment.net_votes += 2
            self.comment.upvotes += 1
            self.comment.downvotes -= 1
        elif self.value == 1 and new_vote_value == -1:  # up to down
            vote_diff = -2
            self.comment.net_votes -= 2
            self.comment.upvotes -= 1
            self.comment.downvotes += 1
        elif self.value == 0 and new_vote_value == 1:
            vote_diff = 1
            self.comment.upvotes += 1
            self.comment.net_votes += 1
        elif self.value == 0 and new_vote_value == -1:
            vote_diff = -1
            self.comment.downvotes += 1
            self.comment.net_votes -= 1
        else:
            return None

        if self.comment.user != request_user:
            self.comment.user.userprofile.comment_karma +=  vote_diff
            self.comment.user.userprofile.save()

        self.value = new_vote_value
        self.save()
        self.comment.save()
        self.comment.user.save()

        return vote_diff

    def unvote(self, request_user):
        if self.value == 1:
            vote_diff = -1
            self.comment.upvotes -= 1
            self.comment.net_votes -= 1
        elif self.value == -1:
            vote_diff = 1
            self.comment.downvotes -= 1
            self.comment.net_votes += 1
        else:
            return None
        if self.comment.user != request_user:
            self.comment.user.userprofile.comment_karma += vote_diff
            self.comment.user.userprofile.save()

        self.value = 0
        self.save()
        self.comment.save()
        self.comment.user.save()
        return vote_diff

class VotePost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    value = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def change_vote(self, new_vote_value, request_user):
        if self.value == -1 and new_vote_value == 1:  # down to up
            vote_diff = 2
            self.post.net_votes += 2
            self.post.upvotes += 1
            self.post.downvotes -= 1
        elif self.value == 1 and new_vote_value == -1:  # up to down
            vote_diff = -2
            self.post.net_votes -= 2
            self.post.upvotes -= 1
            self.post.downvotes += 1
        elif self.value == 0 and new_vote_value == 1:
            vote_diff = 1
            self.post.upvotes += 1
            self.post.net_votes += 1
        elif self.value == 0 and new_vote_value == -1:
            vote_diff = -1
            self.post.downvotes += 1
            self.post.net_votes -= 1
        else:
            return None

        if self.post.user != request_user:
            self.post.user.userprofile.submission_karma +=  vote_diff
            self.post.user.userprofile.save()

        self.value = new_vote_value
        self.save()
        self.post.save()
        self.post.user.save()

        return vote_diff

    def unvote(self, request_user):
        if self.value == 1:
            vote_diff = -1
            self.post.upvotes -= 1
            self.post.net_votes -= 1
        elif self.value == -1:
            vote_diff = 1
            self.post.downvotes -= 1
            self.post.net_votes += 1
        else:
            return None
        if self.post.user != request_user:
            self.post.user.userprofile.submission_karma += vote_diff
            self.post.user.userprofile.save()

        self.value = 0
        self.save()
        self.post.save()
        self.post.user.save()
        return vote_diff