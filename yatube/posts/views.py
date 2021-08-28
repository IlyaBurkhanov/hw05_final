from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

page_count = settings.GLOBALS['page_count']


def index(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, page_count)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Последние обновления на сайте'
    context = {
        'page_obj': page_obj,
        'title': title,
        'headline': title,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.post_group.all()
    page_obj = Paginator(posts, page_count).get_page(request.GET.get('page'))
    title = 'Записи сообщества ' + str(group)
    context = {
        'page_obj': page_obj, #page_obj
        'title': title,
        'group': group
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.post_author.all()
    page_obj = Paginator(posts, page_count).get_page(request.GET.get('page'))
    following = request.user in [x.user for x in author.following.all()]
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post_count = post.author.post_author.count()
    context = {
        'post': post,
        'post_count': post_count,
        'comments': post.comments.all(),
        'form': CommentForm()
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    request.FILES or None
                    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)  # main
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:profile', username=post.author)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    return render(request, 'posts/create_post.html',
                  {'form': form, 'is_edit': True})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    posts = Post.objects.filter(
        author__in=[
            x.author for x in Follow.objects.filter(user=request.user)])
    page_obj = Paginator(posts, page_count).get_page(request.GET.get('page'))
    title = 'Авторы на которых вы подписаны'
    context = {
        'page_obj': page_obj,
        'title': title,
        'headline': title,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    if request.user.username != username:
        Follow.objects.get_or_create(
            user=request.user,
            author=User.objects.get(username=username))
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    follow = Follow.objects.get(user=request.user,
                                author=User.objects.get(username=username))
    if follow:
        follow.delete()
    return redirect('posts:follow_index')
