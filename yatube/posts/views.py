from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods, require_GET

from .models import Post, Group, Follow
from .forms import PostForm, CommentForm

User = get_user_model()


@require_GET
@cache_page(20, key_prefix="index_page")
def index(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "posts/index.html", {"page": page})


@require_GET
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "posts/group.html", {"group": group, "page": page})


@require_GET
def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    count = paginator.count
    following = False
    followers_count = Follow.objects.filter(author=author).count()
    following_count = Follow.objects.filter(user=author).count()
    button = True
    if request.user.username == username:
        button = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user, author=author)
    context = {
        "author": author,
        "count": count,
        "page": page,
        "following": following,
        "followers_count": followers_count,
        "following_count": following_count,
        "button": button
    }
    return render(request, "posts/profile.html", context)


@require_http_methods(["GET", "POST"])
def post_view(request, username, post_id):
    user = get_object_or_404(User, username=username)
    count = user.posts.count()
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    following = False
    followers_count = Follow.objects.filter(author=user).count()
    following_count = Follow.objects.filter(user=user).count()
    if request.user.is_authenticated:
        following = True
    context = {
        "author": user,
        "post": post,
        "count": count,
        "comments": comments,
        "form": form,
        "following": following,
        "followers_count": followers_count,
        "following_count": following_count,
    }
    return render(request, "posts/post.html", context)


@require_http_methods(["GET", "POST"])
@login_required
def new_post(request):
    author = request.user
    form = PostForm(request.POST or None, files=request.FILES)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = author
        post.save()
        return redirect("index")
    return render(request, "posts/new_post.html", {"form": form})


@require_http_methods(["GET", "POST"])
@login_required
def post_edit(request, username, post_id):
    user = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id, author=user)

    if request.user == post.author:
        form = PostForm(
            request.POST or None, files=request.FILES or None, instance=post
        )

        if form.is_valid():
            post.save()
            return redirect("post", username=username, post_id=post_id)

        context = {"form": form, "post": post, "is_edit": True}
        return render(request, "posts/new_post.html", context)

    return redirect("post", username=username, post_id=post_id)


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@require_http_methods(["GET", "POST"])
@login_required
def add_comment(request, username, post_id):
    comment_author = request.user
    post_author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, author=post_author, id=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = comment_author
        comment.post = post
        comment.save()
        return redirect("post", username=username, post_id=post_id)
    return render(request, "posts/comments.html", {"form": form, "post": post})


@require_GET
@login_required
def follow_index(request):
    user = get_object_or_404(User, username=request.user.username)
    follow = Follow.objects.filter(user=user)
    authors = []
    for obj in follow:
        authors.append(obj.author)
    posts = []
    for author in authors:
        posts += Post.objects.filter(author=author)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "posts/follow.html", {"page": page})


@require_http_methods(["GET", "POST"])
@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    if author == user:
        return redirect("profile", username)
    elif Follow.objects.filter(user=user, author=author).exists():
        return redirect("profile", username)
    Follow.objects.create(user=user, author=author)
    return redirect("profile", username)


@require_http_methods(["GET", "POST"])
@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.get(user=user, author=author)
    follow.delete()
    return redirect("profile", username)
