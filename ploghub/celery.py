from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ploghub.settings')

app = Celery('ploghub', broker='redis://localhost:6379/0')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0, update_rank.s(), name="Update rank", expires=10)
    sender.add_periodic_task(60.0, rebuild_tree.s(), name="Rebuild comment tree", expires=10)

@app.task
def update_rank():
    from ploghubapp.models import Post, Comment
    from django.db.models import Count
    posts = Post.objects.filter(deleted=False).annotate(comments_count=Count('comment'))
    for post in posts:
        post.calculate_rank(post.comments_count)

@app.task
def rebuild_tree():
    from ploghubapp.models import Comment
    from django.db import transaction
    with transaction.atomic():
        Comment.objects.rebuild()