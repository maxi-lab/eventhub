import datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.http import HttpResponseServerError
from .models import Event, User, Comment, Ticket, RefundRequest
from django.http import HttpResponseForbidden
from .models import RefundRequest
from .models import Event, User, Ticket, Venue
from django.http import HttpResponseForbidden, HttpResponse
from .models import Event, User, UserNotification, Notification
from .models import Category
from django.db.models import Count

def is_admin(user):
    return user.is_organizer

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

    return render(request, "app/event_detail.html", {"event": event, "user_comments": user_comments, "other_comments": other_comments, "comments_count": comments_count, "user_is_organizer": request.user.is_organizer})


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

def event_tickets(request,id):
    if not request.user.is_organizer:
        return redirect("events")
    event = get_object_or_404(Event, pk=id)
    tickets = Ticket.objects.filter(event=event,is_deleted=False).order_by("buy_date")
    for ticket in tickets:
        print(ticket.is_deleted)
    return render(request, "app/event_tickets.html", {"event": event, "tickets": tickets})

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
        category = get_object_or_404(Category, pk=request.POST.get("category"))

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.new(title, description, scheduled_at, request.user, category)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user, category)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    categories = Category.objects.filter(is_active=True)
    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer, "categories":categories},
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
def mark_all_notifications_read(request):
    if request.method == 'POST':
        UserNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('notifications_user')

@login_required
def mark_notification_read(request, pk):
    notif = get_object_or_404(UserNotification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    return redirect('notifications_user')

@login_required
def notifications_user(request):
    user_notifications = UserNotification.objects.filter(
        user=request.user,
        notification__is_deleted=False
    ).select_related('notification').order_by('-notification__created_at')

    new_count = user_notifications.filter(is_read=False).count()

    return render(request, 'app/notifications_user.html', {
        'user_notifications': user_notifications,
        'new_count': new_count,
    })

@login_required
def notifications_organizer(request):
    events = Event.objects.all()
    event_filter = request.GET.get('event', '')
    priority_filter = request.GET.get('priority', '')
    search_filter = request.GET.get('title', '')

    notifications = Notification.objects.filter(is_deleted=False)

    if event_filter:
        notifications = notifications.filter(event__id=event_filter)

    if priority_filter:
        notifications = notifications.filter(priority=priority_filter)

    if search_filter:
        notifications = notifications.filter(title__icontains=search_filter)

    return render(request, "app/notifications_organizer.html", {
        "notifications": notifications,
        "events": events,
        "selected_event": event_filter,
        "selected_priority": priority_filter,
        "search_filter": search_filter
    })

@login_required
def notifications_delete(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    notification.is_deleted = True
    notification.save()
    return redirect('notifications_organizer')


@login_required
def notifications_form(request, pk=None):
    if pk:
        notification = get_object_or_404(Notification, pk=pk)
        is_edit = True
    else:
        notification = None
        is_edit = False

    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        event_id = request.POST.get('event')
        priority = request.POST.get('priority')
        recipients_type = request.POST.get('recipients') 
        user_id = request.POST.get('user')

        if not title or not message:
            messages.error(request, "Título y mensaje son obligatorios.")
            return redirect(request.path)

        if not is_edit:
            if recipients_type == 'all' and not event_id:
                messages.error(request, "Debes seleccionar un evento si deseas notificar a todos los asistentes.")
                return redirect(request.path)

            if recipients_type == 'user' and not user_id:
                messages.error(request, "Debes seleccionar un usuario específico.")
                return redirect(request.path)

        event = get_object_or_404(Event, pk=event_id) if event_id else None

        if is_edit:
            notification.title = title
            notification.message = message
            notification.priority = priority
            notification.save()
        else:
            notification = Notification.objects.create(
                title=title,
                message=message,
                event=event,
                priority=priority
            )

            if recipients_type == 'all':
                users = User.objects.filter(tickets__event=event).distinct()
            else:
                users = [get_object_or_404(User, pk=user_id)]

            for user in users:
                UserNotification.objects.create(user=user, notification=notification)

        return redirect('notifications_organizer')

    return render(request, 'app/notifications_form.html', {
        'notification': notification,
        'is_edit': is_edit,
        'events': Event.objects.all(),
        'users': User.objects.all(),
    })

    
def tickets(request):
    user=request.user
    if user.is_organizer:
        events = Event.objects.filter(organizer=user).order_by("scheduled_at")
        tickets = Ticket.objects.filter(is_deleted=False).order_by("buy_date")
        for t in tickets:
            if t.event not in events:
                tickets=tickets.exclude(pk=t.pk)
                
    else:
        tickets = Ticket.objects.filter(is_deleted=False,user=user).order_by("buy_date")

    
    tipo=Ticket.TICKET_TYPES
    return render(request, "app/tickets.html", {"tickets": tickets, "tipo": tipo})

def ticket_form(request,id=None):
    ticket = {}
    events = Event.objects.all()
    user=request.user
    if id is not None:
        ticket=get_object_or_404(Ticket, pk=id)
    if request.method == "POST":
        tipo_ticket=request.POST.get("type_ticket")
        event_id=request.POST.get("event_id")
        quantity=int(request.POST.get("quantity"))
        if quantity < 1:
            return render(request,'app/ticket_form.html',{"events":events,"ticket":ticket,"error":"La cantidad de tickets debe ser mayor a 0"})
        card=verify_card(request.POST.get("card_number"),request.POST.get("expiration_date"),request.POST.get("cvv"))
        if len(card)!=0:
            
            e=''
            for i in card:
                e=e+' '+card[i]
            
            return render(request,'app/ticket_form.html',{"events":events,"ticket":ticket,"error":e})
        
        event=get_object_or_404(Event, pk=event_id)
        if id is None:
            print("Creando nuevo ticket")
            Ticket.new(tipo_ticket,event,user,quantity)
            return redirect("tickets")
        Ticket.update_ticket(id, tipo_ticket, event,quantity=quantity)
        return redirect("tickets")
    return render(request, "app/ticket_form.html", {"events":events,"ticket":ticket})
def ticket_delete(request, id):
    if request.method == "POST":
        Ticket.delete_ticket(id)
        return redirect("tickets")
    return redirect("tickets")
def ticket_detail(request, id):
    ticket = get_object_or_404(Ticket, pk=id)
    tipos=Ticket.TICKET_TYPES
    return render(request, "app/ticket_detail.html", {"ticket": ticket,"tipos":tipos})

def verify_card(number, expiration_date, cvv,):
    errors={}
    if number is None or expiration_date is None or cvv is None:
        errors["number"] = "El número de tarjeta no puede ser nulo"
        errors["expiration_date"] = "La fecha de expiración no puede ser nula"
        errors["cvv"] = "El CVV no puede ser nulo"
        return errors
    if len(number) != 16 or number.isdigit() == False:
        errors["number"] = "El número de tarjeta debe tener 16 dígitos"
    if len(cvv) != 3:
        errors["cvv"] = "El CVV debe tener 3 dígitos"
    if len(expiration_date) != 5:
        errors["expiration_date"] = "La fecha de expiración debe tener el formato MM/AA"
    return errors
def terms_policy(request):
    return render(request, "app/terms.html", {})


@login_required
def create_refund_request(request):
    if request.method == "POST":
        ticket_code = request.POST.get("ticket_code")
        reason = request.POST.get("reason")

        success, errors = RefundRequest.create_request(request.user, ticket_code, reason)
        if success:
            return redirect("my_refund_requests")
        return render(request, "app/refund_create.html", {"errors": errors, "ticket_code": ticket_code, "reason": reason})

    return render(request, "app/refund_create.html")


@login_required
def my_refund_requests(request):
    user=request.user
    if user.is_organizer:
        return redirect("manage_refund_requests")
    requests = RefundRequest.objects.filter(ticket__user=request.user, is_deleted=False).order_by("-created_at")
    return render(request, "app/refund_my_list.html", {"refund_requests": requests})


@login_required
def edit_refund_request(request, request_id):
    refund = get_object_or_404(RefundRequest, id=request_id, is_deleted=False)

    if refund.ticket.user != request.user:
        return HttpResponseForbidden("No tienes permiso para editar esta solicitud.")

    if request.method == "POST":
        new_reason = request.POST.get("reason")
        success, errors = RefundRequest.edit_request(request.user, request_id, new_reason)
        if success:
            return redirect("my_refund_requests")
        return render(request, "app/refund_edit.html", {"refund": refund, "errors": errors})

    return render(request, "app/refund_edit.html", {"refund": refund})


@login_required
def delete_refund_request(request, request_id):
    refund = get_object_or_404(RefundRequest, id=request_id, is_deleted=False)

    if refund.ticket.user != request.user:
        return HttpResponseForbidden("No tienes permiso para eliminar esta solicitud.")

    if request.method == "POST":
        success, errors = RefundRequest.delete_request(request.user, request_id)
        if success:
            return redirect("my_refund_requests")
        return render(request, "app/refund_delete.html", {"refund": refund, "errors": errors})

    return render(request, "app/refund_delete.html", {"refund": refund})


@login_required
@user_passes_test(is_admin, login_url='/events', redirect_field_name=None)
def manage_refund_requests(request):
    refunds = RefundRequest.objects.filter(is_deleted=False).order_by("-created_at")

    if request.method == "POST":
        request_id = request.POST.get("request_id")
        new_status = request.POST.get("new_status")
        refund = get_object_or_404(RefundRequest, id=request_id)

        success, errors = refund.change_status(new_status, request.user)
        if not success:
            return render(request, "app/refund_manage.html", {"refund_requests": refunds, "errors": errors})

        return redirect("manage_refund_requests")

    return render(request, "app/refund_manage.html", {"refund_requests": refunds})

@login_required
def refund_request_detail(request, request_id):
    refund = get_object_or_404(RefundRequest, id=request_id, is_deleted=False)

    if refund.ticket.user != request.user and not request.user.is_organizer:
        return HttpResponseForbidden("No tenés permiso para ver esta solicitud.")

    return render(request, "app/refund_detail.html", {"refund": refund})

def categories(request):
    categories = Category.objects.annotate(event_count=Count('events'))
    return render(
        request,
        "app/categories.html",
        {"categories": categories, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def category_detail(request, id):
    category = get_object_or_404(Category, pk=id)
    events = Event.objects.filter(category=category)
    return render(request, "app/category_detail.html", {"category": category, 'events':events})


@login_required
def category_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("categories")

    if request.method == "POST":
        category = get_object_or_404(Category, pk=id)
        category.delete()
        return redirect("categories")

    return redirect("categories")


@login_required
def category_form(request, id=None):
    user = request.user
    print(f"{request.method} de categoria {id}")

    if not user.is_organizer:
        return redirect("categories")

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        is_active = request.POST.get("is_active") is not None
        print(f"{name} - {description} {is_active}")


        if id is None:
            Category.new(name, description, is_active)
        else:
            category = get_object_or_404(Category, pk=id)
            category.update(name, description, is_active)

        return redirect("categories")

    category = {}
    if id is not None:
        category = get_object_or_404(Category, pk=id)

    return render(
        request,
        "app/category_form.html",
        {"category": category, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def list_venues(request):
    venues = Venue.objects.all()
    return render(request, 'app/venue_list.html', {'venues': venues})

@login_required
def create_venue(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        capacity = request.POST.get('capacity')
        contact = request.POST.get('contact')

        if not name or not address or not city or not capacity or not contact:
            return HttpResponse("Todos los campos son obligatorios", status=400)

        venue = Venue.objects.create(
            name=name,
            address=address,
            city=city,
            capacity=capacity,
            contact=contact
        )

        return redirect('list_venues')

    return render(request, 'app/venue_form.html')

def edit_venue(request, id):
    venue = get_object_or_404(Venue, id=id)
    
    if request.method == 'POST':
        venue.name = request.POST.get('name')
        venue.address = request.POST.get('address')
        venue.city = request.POST.get('city')
        venue.capacity = request.POST.get('capacity')
        venue.contact = request.POST.get('contact')
        venue.save()

        return redirect('list_venues')

    return render(request, 'app/venue_edit.html', {'venue': venue})

@login_required
def delete_venue(request, id):
    venue = get_object_or_404(Venue, id=id)
    
    if request.method == 'POST':
        venue.delete()
        return redirect('list_venues')

    return render(request, 'app/venue_confirm_delete.html', {'venue': venue})

@login_required
def venue_detail(request, venue_id):
    venue = get_object_or_404(Venue, pk=venue_id)
    return render(request, 'app/venue_detail.html', {'venue': venue})