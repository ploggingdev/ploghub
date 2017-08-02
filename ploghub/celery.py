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

@app.task
def update_rank():
    from ploghubapp.models import Post
    posts = Post.objects.filter(deleted=False)
    for post in posts:
        post.calculate_rank()