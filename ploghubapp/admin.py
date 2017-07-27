from django.contrib import admin
from .models import Post
from simple_history.admin import SimpleHistoryAdmin
from .forms import AdminPostForm

@admin.register(Post)
class PostAdmin(SimpleHistoryAdmin):
    form = AdminPostForm
    list_display = ('title','body', 'deleted','user' ,'created')