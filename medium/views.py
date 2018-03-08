from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.utils import timezone

import re

from medium.forms import (UserForm, UserProfileForm, PostForm,
                          UserEditForm, PostFeaturedImageForm, CommentForm)
from medium.models import Post, UserProfile, Comment, Topic
# Create your views here.


class IndexView(generic.ListView):
    template_name = 'medium/index.html'
    context_object_name = 'posts_list'

    def get_queryset(self):
        return Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')


class NewPostView(LoginRequiredMixin, generic.CreateView):
    login_url = '/login/'
    redirect_field_name = 'medium/post.html'
    template_name = 'medium/new_post.html'
    form_class = PostForm
    model = Post

    def form_valid(self, form):
        form.instance.author = self.request.user
        if form.instance.topics_raw:
            print(form.instance.topics_raw)
            topics = form.instance.topics_raw.split(',')
            print(topics)
        return super().form_valid(form)


class PostDeleteView(LoginRequiredMixin, generic.DeleteView):
    login_url = '/login/'
    model = Post
    success_url = reverse_lazy('medium:index')


class PostDetailView(generic.DetailView):
    model = Post
    template_name = 'medium/post.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        return context


class PostEditView(LoginRequiredMixin, generic.UpdateView):
    login_url = '/login/'
    redirect_field_name = 'medium/post.html'
    template_name = 'medium/new_post.html'
    form_class = PostForm
    model = Post

    def form_valid(self, form):
        if form.instance.topics_raw:
            print(form.instance.topics_raw)
            topics = form.instance.topics_raw.split(',')
            post = Post.objects.get(pk=form.instance.id)
            for topic in topics:
                # check if topic exists
                topic = topic.strip()
                new_topic = Topic.objects.filter(tags=topic)

                if new_topic:
                    print('already have this topic')
                else:
                    print('adding topic')
                    new_topic = Topic(tags=topic)

                # TODO make unique key for adding tags
                
                # else:
                #     new_topic = Topic(tags=topic)

                #     new_topic.save()
                # if topic in post.topics.all():
                #     print('already here')
                # form.instance.save()
                # form.instance.topics.add(new_topic)
        return super().form_valid(form)


def add_comment(request, pk):
    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = Post.objects.get(pk=pk)
            comment.author = request.user
            comment.save()
    return HttpResponseRedirect(reverse('medium:post', kwargs={'pk': pk}))


def register_user(request):
    registered = False

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        user_profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and user_profile_form.is_valid():
            new_user = user_form.save()
            new_user.set_password(new_user.password)
            new_user.save()

            new_user_profile = user_profile_form.save(commit=False)
            new_user_profile.user = new_user

            if 'avatar' in request.FILES:
                new_user_profile.avatar = request.FILES['avatar']

            new_user_profile.save()
            registered = True
        else:
            print(user_form.errors, user_profile_form.errors)
    else:
        user_form = UserForm()
        user_profile_form = UserProfileForm()
    return render(request, 'medium/registration.html', {
        'user_form': user_form,
        'user_profile_form': user_profile_form,
        'registered': registered
    })


def new_post(request):

    if request.method == 'POST':
        post_form = PostForm(data=request.POST)
        post_featured_image_form = PostFeaturedImageForm(data=request.POST)
        if post_form.is_valid() and post_featured_image_form.is_valid():
            post = post_form.save(commit=False)
            post.author = request.user
            post.save()

            if 'featured_image' in request.FILES:

                post.avatar = request.FILES['featured_image']
                post.save()

    else:
        post_form = PostForm()
        post_featured_image_form = PostFeaturedImageForm()

    return render(request, 'medium/new_post.html', {
        'form': post_form,
        'featured_form': post_featured_image_form,

    })


def search_posts(request):
    if request.method == 'POST':
        search = request.POST.get('search')
        posts_list = Post.objects.filter(Q(published_date__lte=timezone.now()),
                                         Q(title__contains=search) | Q(content__contains=search)).order_by('-published_date')

        return render(request, 'medium/index.html', {'posts_list': posts_list})
    else:
        return HttpResponseRedirect(reverse('medium:index'))


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('medium:index'))
        else:
            return HttpResponse('invalid login details')
    else:
        return render(request, 'medium/login.html')


@login_required
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.publish()
    return HttpResponseRedirect(reverse('medium:post', kwargs={'pk': pk}))


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('medium:index'))


@login_required
def profile_edit(request):

    if request.method == 'POST':
        user_form = UserForm(data=request.POST, instance=request.user)
        user_profile_form = UserProfileForm(
            data=request.POST, instance=request.user.profile)

        if user_form.is_valid() and user_profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            user_profile = user_profile_form.save(commit=False)
            user_profile.user = user

            if 'avatar' in request.FILES:
                user_profile.avatar = request.FILES['avatar']

            user_profile.save()

    user_form = UserEditForm(instance=request.user)
    user_profile_form = UserProfileForm(instance=request.user.profile)
    return render(request, 'medium/profile_edit.html', {
        'user_profile_form': user_profile_form,
        'user_form': user_form,
    })


@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post.pk
    comment.delete()
    return redirect('medium:post', pk=post_pk)
