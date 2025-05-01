import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Event, User, Comment


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        is_organizer = request.POST.get("is-organizer") is not None
        password = request.POST.get("password")
        password_confirm = request.POST.get("password-confirm")

        errors = User.validate_new_user(email, username, password, password_confirm)

        if len(errors) > 0:
            return render(
                request,
                "accounts/register.html",
                {
                    "errors": errors,
                    "data": request.POST,
                },
            )
        else:
            user = User.objects.create_user(
                email=email, username=username, password=password, is_organizer=is_organizer
            )
            login(request, user)
            return redirect("events")

    return render(request, "accounts/register.html", {})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request, "accounts/login.html", {"error": "Usuario o contraseña incorrectos"}
            )

        login(request, user)
        return redirect("events")

    return render(request, "accounts/login.html")


def home(request):
    return render(request, "home.html")


@login_required
def events(request):
    events = Event.objects.all().order_by("scheduled_at")
    return render(
        request,
        "app/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer, "user_id": request.user.id},
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    user_comments = Comment.objects.filter(event = event, user = request.user).exclude(isDeleted = True)
    other_comments = Comment.objects.filter(event = event, isDeleted=False).exclude(user = request.user)
    comments_count = user_comments.count() + other_comments.count()

    return render(request, "app/event_detail.html", {"event": event, "user_comments": user_comments, "other_comments": other_comments, "comments_count": comments_count})


@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        event.delete()
        return redirect("events")

    return redirect("events")


@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.new(title, description, scheduled_at, request.user)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def save_comment(request, id):
    if request.method == "POST":
        title = request.POST.get('title')
        text = request.POST.get('text')
        event = get_object_or_404(Event, id=id)

        Comment.objects.create(
            title=title,
            text=text,
            user=request.user,
            event=event,
        )
        return redirect('event_detail', id=id)
    return redirect('events')

@login_required
def edit_comment(request, id):
    comment = get_object_or_404(Comment, id = id, user = request.user)

    if (request.method == "POST"):
        comment.title = request.POST.get('title') or comment.title
        comment.text = request.POST.get('text') or comment.text
        comment.save()
        return redirect('event_detail', id=comment.event.id)
    return redirect('event_detail', id=comment.event.id)

@login_required
def delete_comment(request, id):
    comment =get_object_or_404(Comment, id = id, user = request.user)

    if (request.method == "POST"):
        comment.isDeleted = True
        comment.save()
        return redirect('event_detail', id=comment.event.id)
    return redirect('event_detail', id=comment.event.id)

@login_required
def admin_delete_comment(request, id):
    comment =get_object_or_404(Comment, id = id)

    if (request.method == "POST"):
        comment.isDeleted = True
        comment.save()
        return redirect('admin_comments')
    return redirect('admin_comments')

@login_required
def admin_comments(request):
    events = Event.objects.filter(organizer = request.user)
    admin_comments = []
    for event in events:
        comments = Comment.objects.filter(isDeleted = False, event=event)
        admin_comments.extend(comments)
    return render(
    request,
    "app/comments.html",
    {"admin_comments": admin_comments},
)