from django.contrib import admin
from .models import Post, UserProfile
from simple_history.admin import SimpleHistoryAdmin
from .forms import AdminPostForm, AdminUserProfileForm

@admin.register(Post)
class PostAdmin(SimpleHistoryAdmin):
    form = AdminPostForm
    list_display = ('title','body', 'deleted','user' ,'created')

@admin.register(UserProfile)
class UserProfileAdmin(SimpleHistoryAdmin):
    form = AdminUserProfileForm
    list_display = ('user' ,'created')