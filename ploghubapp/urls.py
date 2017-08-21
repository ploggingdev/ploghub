from django.conf.urls import url, include
from django.contrib.auth import views as auth_views

from . import views

app_name = 'ploghubapp'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='home_page'),
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
    url(r'^profile/$', views.ProfileView.as_view(), name='profile'),
    url(r'^profile/(?P<username>[a-zA-Z0-9-_]+)/$', views.PublicUserProfileView.as_view(), name='public_user_profile'),
    url(
        r'^login/$',
        auth_views.login, { 'redirect_authenticated_user' : True}, name="login",
    ),
    url(
        r'^logout/$',
        views.LogoutView.as_view(), name="logout"
    ),
    url(
        r'^password_change/$',
        auth_views.password_change, {'post_change_redirect' : '/password_change/done'} ,name="password_change"
    ),
    url(
        r'^password_change/done/$',
        auth_views.password_change_done ,name="password_change_done"
    ),
    url(
        r'^password_reset/$',
        auth_views.password_reset, {'post_reset_redirect' : '/password_reset/done', 'from_email' : 'ploghub@ploggingdev.com'} ,name="password_reset"
    ),
    url(
        r'^password_reset/done/$',
        auth_views.password_reset_done, name="password_reset_done"
    ),
    url(
        r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm, {'post_reset_redirect' : '/reset/done'}, name="password_reset_confirm"
    ),
    url(
        r'^reset/done/$',
        auth_views.password_reset_complete, name="password_reset_complete"
    ),
    url(r'^write/$', views.WriteView.as_view(), name='write'),
    url(r'^post/(?P<pk>[0-9]+)/(?P<username>.+)/(?P<slug>[a-zA-Z0-9_-]+)/$', views.ViewPost.as_view(), name='view_post'),
    url(r'^comment/(?P<pk>[0-9]+)/reply/$', views.ReplyCommentView.as_view(), name='reply_to_comment'),
    url(r'^comment/(?P<pk>[0-9]+)/edit/$', views.EditCommentView.as_view(), name='edit_comment'),
    url(r'^comment/(?P<pk>[0-9]+)/delete/$', views.DeleteCommentView.as_view(), name='delete_comment'),
    url(r'^myposts/$', views.MyPosts.as_view(), name='my_posts'),
    url(r'^votecomment/(?P<pk>[0-9]+)/$', views.VoteCommentView.as_view(), name='vote_comment'),
    url(r'^votepost/(?P<pk>[0-9]+)/$', views.VotePostView.as_view(), name='vote_post'),
    url(r'^post/(?P<pk>[0-9]+)/edit/$', views.EditPostView.as_view(), name='edit_post'),
    url(r'^post/(?P<pk>[0-9]+)/delete/$', views.DeletePostView.as_view(), name='delete_post'),
    url(r'^about/$', views.AboutView.as_view(), name='about'),
]