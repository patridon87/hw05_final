from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods, require_GET

from .models import Post, Group, Follow
from .forms import PostForm, CommentForm

User = get_user_model()

def is_following(user, author):
    if Follow.objects.filter(user=user, author=author):
        return True
    return False

@require_GET
def index(request):
    posts = cache.get("index-page")
    if posts is None:
        posts = Post.objects.all()
        cache.set("index-page", posts, timeout=20)
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
    followers_count = author.following.count()
    following_count = author.follower.count()
    follow_button_display = request.user.username != username


    if request.user.is_authenticated:
        following = is_following(user=request.user, author=author)

    context = {
        "author": author,
        "count": count,
        "page": page,
        "following": following,
        "followers_count": followers_count,
        "following_count": following_count,
        "follow_button_display": follow_button_display
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
    followers_count = user.following.count()
    following_count = user.follower.count()
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

    if request.user != post.author:
        return redirect("post", username=username, post_id=post_id)

    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )

    if form.is_valid():
        post.save()
        return redirect("post", username=username, post_id=post_id)

    context = {"form": form, "post": post, "is_edit": True}
    return render(request, "posts/new_post.html", context)





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

    follows = list(user.follower.all())
    authors = [follow.author for follow in follows]

    posts = Post.objects.filter(author__in=authors)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(request, "posts/follow.html", {"page": page})


@require_http_methods(["GET", "POST"])
@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect("profile", username)


@require_http_methods(["GET", "POST"])
@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect("profile", username)
