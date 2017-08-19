from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .forms import RegisterForm, ProfileForm
from django.contrib.auth import views, authenticate, login, get_user_model
from django.contrib import messages
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core import exceptions
from django.views import generic
from .forms import PostModelForm, CommentForm, CommentEditForm, CommentReplyForm
from .models import Post, Comment, VoteComment, UserProfile, VotePost
import markdown
import bleach
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from itertools import chain
from operator import attrgetter
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count

class IndexView(generic.ListView):
    model = Post
    paginate_by = 10
    template_name = 'ploghubapp/home_page.html'

    def get(self, request):
        if request.GET.get('sort_by') == "new":
            all_results = self.model.objects.filter(deleted=False).order_by('-created').annotate(comments_count=Count('comment'))
            sort_by = "New"
        else:
            sort_by = "Popular"
            all_results = self.model.objects.filter(deleted=False).order_by('-rank').annotate(comments_count=Count('comment'))

        paginator = Paginator(all_results, self.paginate_by)

        page = request.GET.get('page')
        try:
            post_list = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            post_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            post_list = paginator.page(paginator.num_pages)
        
        if request.user.is_authenticated:
            user_votes = VotePost.objects.filter(user=request.user)
        else:
            user_votes = list()

        return render(request, self.template_name, {'post_list' : post_list, 'sort_by' : sort_by, 'user_votes' : user_votes })


class LogoutView(LoginRequiredMixin, View):

    def get(self, request):
        template_response = views.logout(request)
        messages.success(request, 'You have been logged out')
        return redirect(reverse('ploghubapp:login'))

class RegisterView(View):
    form_class  = RegisterForm
    template_name = 'registration/register.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form' : form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            new_username = form.cleaned_data['username']
            new_password = form.cleaned_data['password']
            new_email = form.cleaned_data['email']

            if get_user_model().objects.filter(username=new_username).exists():
                messages.error(request, "Username not available, choose a different one")
                return render(request, self.template_name, {'form' : form})
            if new_email != '' and get_user_model().objects.filter(email=new_email).exists():
                messages.error(request, "Email not available, choose a different one")
                return render(request, self.template_name, {'form' : form})
            
            #validate password
            try:
                validate_password(new_password)
            except exceptions.ValidationError as e:
                form.errors['password'] = list(e.messages)
                return render(request, self.template_name, {'form' : form})

            user = get_user_model().objects.create_user(username=new_username, password=new_password, email=new_email)
            user = authenticate(username=new_username, password=new_password)
            userprofile = UserProfile(user=user)
            userprofile.save()
            if user is not None:
                login(request, user)
                return redirect(reverse('ploghubapp:profile'))
        else:
            return render(request, self.template_name, {'form' : form})

class ProfileView(LoginRequiredMixin, View):
    login_url = '/user/login/'
    form_class = ProfileForm
    template_name = 'registration/profile.html'

    def get(self, request, *args, **kwargs):
        data = {'about' : request.user.userprofile.about}
        if request.user.email != '':
            data['email'] = request.user.email
        form = self.form_class(initial = data)
        return render(request, self.template_name, {'form' : form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, initial={'email' : request.user.email, 'about' : request.user.userprofile.about})
        if form.is_valid():
            if form.has_changed():
                user = request.user
                
                for field in form.changed_data:
                    if field == 'email':
                        if form.cleaned_data[field] != '' and User.objects.filter(email=form.cleaned_data[field]).exclude(id=user.id).exists():
                            messages.error(request, "Email address is already in use")
                            return redirect(reverse('ploghubapp:profile'))
                    setattr(user, field, form.cleaned_data[field])
                user.save()
                user.userprofile.about = form.cleaned_data['about']
                user.userprofile.save()
                messages.success(request, "Profile has been updated")
                return redirect(reverse('ploghubapp:profile'))
            else:
                messages.info(request, "Data has not been changed")
                return redirect(reverse('ploghubapp:profile'))
        else:
            messages.error(request, "Invalid form data")
            return redirect(reverse('ploghubapp:profile'))

class PublicUserProfileView(View):
    template_name = 'registration/public_user_profile.html'

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        return render(request, self.template_name, {'user' : user})

class WriteView(LoginRequiredMixin, View):
    form_class  = PostModelForm
    template_name = 'ploghubapp/write.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form' : form})

    def post(self, request):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            title = form.cleaned_data['title']
            body = form.cleaned_data['body']
            body_html = markdown.markdown(body)
            body_html = bleach.clean(body_html, tags=settings.ARTICLE_TAGS, strip=True)
            article = Post(title=title, body=body, user=request.user, body_html=body_html)

            article.save()
            vote_obj = VotePost(user=request.user,
                                post=article,
                                value=1)
            vote_obj.save()
            article.upvotes += 1
            article.net_votes += 1
            article.save()
            messages.success(request, 'Article has been submitted.')
            return redirect(reverse('ploghubapp:home_page') + '?sort_by=new')
        else:
            return render(request, self.template_name, {'form' : form})

class ViewPost(generic.DetailView):

    template_name = 'ploghubapp/view_post.html'
    form_class = CommentForm

    def get(self, request, pk, username, slug):
        post = get_object_or_404(Post, pk=pk)
        if post.deleted:
            messages.error(request, 'The post you tried to access has been deleted.')
            return redirect(reverse('ploghubapp:home_page', args=[name]))
        nodes = Comment.objects.filter(post=post).filter(deleted=False)
        if request.user.is_authenticated:
            user_votes = VoteComment.objects.filter(user=request.user).filter(comment__post=post)
            try:
                post_vote_value = VotePost.objects.get(post=post, user=request.user).value
            except ObjectDoesNotExist:
                post_vote = None
        else:
            user_votes = list()
        form = self.form_class()
        return render(request, self.template_name, {'post' : post, 'nodes' : nodes, 'form' : form, 'comments_count' : len(nodes), 'user_votes' : user_votes ,'post_vote_value' : post_vote_value })

    def post(self, request, pk, username, slug):
        if not request.user.is_authenticated:
            return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

        form = self.form_class(request.POST)
        if form.is_valid():
            post = get_object_or_404(Post, pk=pk)
            if post.deleted:
                messages.error(request, 'The post that you tried to access has been deleted.')
                return redirect(reverse('ploghubapp:view_post', args=[pk, username, slug]))
            comment_text = form.cleaned_data['comment']
            comment_text_html = markdown.markdown(comment_text)
            comment_text_html = bleach.clean(comment_text_html, tags=settings.COMMENT_TAGS, strip=True)
            
            comment = Comment(comment_text=comment_text, comment_text_html=comment_text_html, user=request.user, post=post)

            comment.save()
            vote_obj = VoteComment(user=request.user,
                                comment=comment,
                                value=1)
            vote_obj.save()
            comment.upvotes += 1
            comment.net_votes += 1
            comment.save()
            messages.success(request, 'Comment has been submitted.')
            return redirect(reverse('ploghubapp:view_post', args=[pk, username, slug]))
        else:
            post = get_object_or_404(Post, pk=pk)
            if post.deleted:
                messages.error(request, 'The post that you tried to access has been deleted.')
                return redirect(reverse('ploghubapp:view_post', args=[pk, username, slug]))
            nodes = Comment.objects.filter(post=post)
            form = self.form_class()
            return render(request, self.template_name, {'post' : post, 'nodes' : nodes, 'form' : form})

class ReplyCommentView(LoginRequiredMixin, generic.View):
    
    template_name = 'ploghubapp/comment_reply.html'
    form_class = CommentReplyForm

    def get(self, request, pk):
        form = self.form_class()
        comment = get_object_or_404(Comment, pk=pk)
        redirect_url = comment.get_post_url()
        if comment.deleted:
            messages.error(request, 'You cannot reply to the comment.')
            return redirect(redirect_url)
        return render(request, self.template_name, {'comment' : comment, 'form' : form, 'redirect_url' : redirect_url})
    
    def post(self, request, pk):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            comment_parent = get_object_or_404(Comment, pk=pk)
            comment_text = form.cleaned_data['comment_text']

            redirect_url = comment_parent.get_post_url()
            if comment_parent.deleted:
                messages.error(request, 'You cannot reply to the comment.')
                return redirect(redirect_url)

            comment_text_html = markdown.markdown(comment_text)
            comment_text_html = bleach.clean(comment_text_html, tags=settings.COMMENT_TAGS, strip=True)
            comment = Comment(comment_text=comment_text, comment_text_html=comment_text_html ,parent=comment_parent, user=request.user, post=comment_parent.post)

            comment.save()
            vote_obj = VoteComment(user=request.user,
                                comment=comment,
                                value=1)
            vote_obj.save()
            comment.upvotes += 1
            comment.net_votes += 1
            comment.save()
            messages.success(request, 'Comment has been submitted.')
            return redirect(redirect_url)
        else:
            comment = get_object_or_404(Comment, pk=pk)
            redirect_url = comment.get_top_level_url()
            if comment.deleted:
                messages.error(request, 'You cannot reply to the comment.')
                return redirect(redirect_url)
            return render(request, self.template_name, {'comment' : comment, 'form' : form, 'redirect_url' : redirect_url})

class EditCommentView(LoginRequiredMixin, generic.View):
    
    template_name = 'ploghubapp/comment_edit.html'
    form_class = CommentEditForm

    def get(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        redirect_url = comment.get_post_url()
        if (not comment.can_edit()) or (comment.user != request.user):
            messages.error(request, 'Invalid request, please try again.')
            return redirect(redirect_url)
        
        form = self.form_class(initial={'comment_text' : comment.comment_text})
        return render(request, self.template_name, {'comment' : comment, 'form' : form, 'redirect_url' : redirect_url})
    
    def post(self, request, pk):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            comment = get_object_or_404(Comment, pk=pk)
            redirect_url = comment.get_post_url()
            if (not comment.can_edit()) or (comment.user != request.user):
                messages.error(request, 'Invalid request, please try again.')
                return redirect(redirect_url)

            comment_text = form.cleaned_data['comment_text']
            
            comment_text_html = markdown.markdown(comment_text)
            comment_text_html = bleach.clean(comment_text_html, tags=settings.COMMENT_TAGS, strip=True)
            comment.comment_text = comment_text
            comment.comment_text_html = comment_text_html

            comment.save()
            messages.success(request, 'Comment has been updated.')
            
            return redirect(redirect_url)
        else:
            comment = get_object_or_404(Comment, pk=pk)
            redirect_url = comment.get_post_url()
            if (not comment.can_edit()) or (comment.user != request.user):
                messages.error(request, 'Invalid request, please try again.')
                return redirect(redirect_url)
            
            return render(request, self.template_name, {'comment' : comment, 'form' : form, 'redirect_url' : redirect_url})

class DeleteCommentView(LoginRequiredMixin, generic.View):
    
    template_name = 'ploghubapp/comment_delete.html'

    def get(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        go_back_url = comment.get_post_url()
        if (not comment.can_delete()) or (comment.user != request.user):
            messages.error(request, 'Invalid request, please try again.')
            return redirect(go_back_url)
        
        return render(request, self.template_name, {'comment' : comment, 'go_back_url' : go_back_url})
    
    def post(self, request, pk):
        
        if request.POST.get('delete_comment'):
            comment = get_object_or_404(Comment, pk=pk)
            redirect_url = comment.get_post_url()
            if comment.can_delete() and comment.user == request.user:
                comment.deleted = True
                comment.save()
                messages.success(request, 'Comment has been deleted.')
            else:
                messages.error(request, 'Comment could not be deleted.')
            return redirect(redirect_url)
        else:
            return redirect(reverse('ploghubapp:home_page'))

class MyPosts(LoginRequiredMixin, generic.View):
    
    template_name = 'ploghubapp/myposts.html'
    paginate_by = 10

    def get(self, request):
        user = request.user
        comments = Comment.objects.all().filter(deleted=False).filter(user=user).order_by('-created')
        posts = Post.objects.all().filter(deleted=False).filter(user=user).order_by('-created')

        total_count = Comment.objects.all().filter(deleted=False).filter(user=user).count() + Post.objects.all().filter(deleted=False).filter(user=user).count()

        all_items = chain(comments, posts)
        all_items = sorted(all_items, key=attrgetter('created'), reverse=True)

        paginator = Paginator(all_items, self.paginate_by)

        page = request.GET.get('page')
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            posts = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            posts = paginator.page(paginator.num_pages)

        return render(request, self.template_name, {'posts': posts})

class VoteCommentView(LoginRequiredMixin, generic.View):

    def post(self, request, pk):
        if request.POST.get('vote_value'):
            try:
                comment = Comment.objects.filter(deleted=False).get(pk=pk)
            except Comment.DoesNotExist:
                return HttpResponseBadRequest()

            vote_value = request.POST.get('vote_value', None)

            try:
                vote_value = int(vote_value)
                if vote_value not in [-1, 1]:
                    raise ValueError("Invalid request")

            except (ValueError, TypeError):
                return HttpResponseBadRequest()

            try:
                vote_obj = VoteComment.objects.get(comment=comment,user=request.user)

            except ObjectDoesNotExist:
                vote_obj = VoteComment(user=request.user,
                                comment=comment,
                                value=vote_value)
                vote_obj.save()
                if vote_value == 1:
                    vote_diff = 1
                    comment.upvotes += 1
                    comment.net_votes += 1
                elif vote_value == -1:
                    vote_diff = -1
                    comment.downvotes += 1
                    comment.net_votes -= 1
                comment.save()

                if comment.user != request.user:
                    comment.user.userprofile.comment_karma +=  vote_diff
                    comment.user.userprofile.save()

                return JsonResponse({'error'   : None,
                                    'vote_diff': vote_diff})
            
            if vote_obj.value == vote_value:
                # cancel vote
                vote_diff = vote_obj.unvote(request.user)
                if not vote_diff:
                    return HttpResponseBadRequest(
                        'Something went wrong while canceling the vote')
            else:
                # change vote
                vote_diff = vote_obj.change_vote(vote_value, request.user)
                if not vote_diff:
                    return HttpResponseBadRequest(
                        'Wrong values for old/new vote combination')
            
            return JsonResponse({'error'   : None,
                         'vote_diff': vote_diff})
        else:
            return HttpResponseBadRequest()

class VotePostView(LoginRequiredMixin, generic.View):

    def post(self, request, pk):
        if request.POST.get('vote_value'):
            try:
                post = Post.objects.filter(deleted=False).get(pk=pk)
            except Post.DoesNotExist:
                return HttpResponseBadRequest()

            vote_value = request.POST.get('vote_value', None)

            try:
                vote_value = int(vote_value)
                if vote_value not in [-1, 1]:
                    raise ValueError("Invalid request")

            except (ValueError, TypeError):
                return HttpResponseBadRequest()

            try:
                vote_obj = VotePost.objects.get(post=post,user=request.user)

            except ObjectDoesNotExist:
                vote_obj = VotePost(user=request.user,
                                post=post,
                                value=vote_value)
                vote_obj.save()
                if vote_value == 1:
                    vote_diff = 1
                    post.upvotes += 1
                    post.net_votes +=  1
                elif vote_value == -1:
                    vote_diff = -1
                    post.downvotes += 1
                    post.net_votes -= 1
                post.save()

                if post.user != request.user:
                    post.user.userprofile.submission_karma +=  vote_diff
                    post.user.userprofile.save()

                return JsonResponse({'error'   : None,
                                    'vote_diff': vote_diff})
            
            if vote_obj.value == vote_value:
                # cancel vote
                vote_diff = vote_obj.unvote(request.user)
                if not vote_diff:
                    return HttpResponseBadRequest(
                        'Something went wrong while canceling the vote')
            else:
                # change vote
                vote_diff = vote_obj.change_vote(vote_value, request.user)
                if not vote_diff:
                    return HttpResponseBadRequest(
                        'Wrong values for old/new vote combination')
            
            return JsonResponse({'error'   : None,
                         'vote_diff': vote_diff})
        else:
            return HttpResponseBadRequest()