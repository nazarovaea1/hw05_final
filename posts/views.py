from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post

User = get_user_model()


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "index.html",
        {"page": page, }
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)

    group_post_list = group.posts.all()
    paginator = Paginator(group_post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html",
        {"group": group, "page": page, }
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect("index")
    return render(request, "new.html", {"form": form})


def profile(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    posts_amount = post_list.count()
    followers = author.following.all().count()
    following = author.follower.all().count()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    following_status = False
    if user.is_authenticated:
        if Follow.objects.filter(user=user, author=author).exists():
            following_status = True
    return render(
        request, "profile.html",
        {"author": author,
         "page": page,
         "posts_amount": posts_amount,
         "followers": followers,
         "following": following,
         "following_status": following_status, }
    )


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id)
    post_list = author.posts.all()
    comments = post.comments.all()
    posts_amount = post_list.count()
    if request.method == "POST" and request.user.is_authenticated:
        add_comment(request, username, post_id)
    form = CommentForm()
    return render(request, "post.html", {"form": form,
                                         "post": post,
                                         "author": author,
                                         "posts_amount": posts_amount,
                                         "comments": comments, })


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if request.user != post.author:
        return redirect("post", username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect("post", username=request.user.username,
                        post_id=post_id)
    return render(
        request, "new.html", {"form": form, "post": post,
                              "is_edited": True},
    )


@login_required
def post_delete(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    post.delete()
    return redirect("index")


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    post_list = post.author.posts.all()
    comments = post.comments.all()
    posts_amount = post_list.count()
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        form.save()
        return redirect("post", username=post.author.username,
                        post_id=post_id)
    # return render(request, "post.html", {"form": form, })
    return render(request, 'post.html', {"form": form,
                                         "post": post,
                                         "author": post.author,
                                         "posts_amount": posts_amount,
                                         "comments": comments, })


@login_required
def comment_delete(request, username, post_id, comment_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    comment = get_object_or_404(Comment, pk=comment_id)
    comment.delete()
    return redirect("post", username=post.author.username,
                    post_id=post_id)


@login_required
def follow_index(request):
    follow_post_list = Post.objects.filter(
        author__following__user=request.user)

    paginator = Paginator(follow_post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {
        "page": page, "paginator": paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    current_user = request.user
    if Follow.objects.all().filter(user=current_user, author=author).exists():
        return redirect("profile", username=author.username)
    if current_user != author:
        Follow.objects.create(user=current_user, author=author)
    return redirect("profile", username=author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    current_user = request.user
    if Follow.objects.filter(user=current_user, author=author).exists():
        Follow.objects.filter(user=current_user, author=author).delete()
    return redirect("profile", username=author.username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
