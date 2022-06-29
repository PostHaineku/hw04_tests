from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, Follow
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .utils import paginate_page
from django.views.decorators.cache import cache_page

User = get_user_model()


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    page_obj = paginate_page(request, post_list)
    context = {
        "page_obj": page_obj
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paginate_page(request, post_list)
    title = group.title
    description = group.description
    context = {
        "page_obj": page_obj,
        "title": title,
        "description": description
    }

    return render(request, "posts/group_list.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related("author")
    template = "posts/profile.html"
    page_obj = paginate_page(request, post_list)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author__username=username).exists()
    context = {
        "page_obj": page_obj,
        "author": author,
        "following": following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comments = post.comments.select_related("post")
    context = {
        "post": post,
        "form": form,
        "comments": comments
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(
            request.POST or None,
            files=request.FILES or None
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            author = request.user.username
            return redirect("posts:profile", author)
        context = {
            "form": form
        }
        return render(request, "posts/create_post.html", context)
    form = PostForm()
    context = {
        "form": form
    }
    return render(request, "posts/create_post.html", context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {
        "form": form,
        "is_edit": True,
        "id": post_id,
    }
    if post.author != request.user:
        return redirect("posts:post_detail", post_id=post_id)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("posts:post_detail", post_id=post_id)
        return render(request, "posts/create_post.html", context)
    return render(request, "posts/create_post.html", context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginate_page(request, post_list)
    context = {
        "page_obj": page_obj
    }
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    follow = get_object_or_404(User, username=username)
    if request.user != follow:
        Follow.objects.get_or_create(user=request.user, author=follow)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect("posts:profile", username=username)
