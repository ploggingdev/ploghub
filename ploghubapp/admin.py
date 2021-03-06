from django.contrib import admin
from .models import Post, UserProfile, Comment, VoteComment, VotePost
from simple_history.admin import SimpleHistoryAdmin
from .forms import AdminPostForm, AdminUserProfileForm, AdminCommentForm
from mptt.admin import MPTTModelAdmin

@admin.register(Post)
class PostAdmin(SimpleHistoryAdmin):
    form = AdminPostForm
    list_display = ('title','body', 'deleted','user' ,'created')

@admin.register(UserProfile)
class UserProfileAdmin(SimpleHistoryAdmin):
    form = AdminUserProfileForm
    list_display = ('user' ,'created')

@admin.register(Comment)
class CommentAdmin(MPTTModelAdmin):
    form = AdminCommentForm
    list_display = ('comment_text','user' ,'created', 'net_votes')

@admin.register(VoteComment)
class VoteCommentAdmin(SimpleHistoryAdmin):
    list_display = ('user', 'value' ,'created')

@admin.register(VotePost)
class VotePostAdmin(SimpleHistoryAdmin):
    list_display = ('user', 'value' ,'created')