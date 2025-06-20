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
from .models import Event, User, UserNotification, Notification, FavoriteEvent
from .models import Category
from django.db.models import Count
from django.urls import reverse


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
    show_favorites = request.GET.get("favorites") == "1"
    show_past = request.GET.get('show_past', 'false') == 'true'
    current_date = timezone.now()

    events = Event.objects.all()

    if show_favorites:
        favorite_event_ids = FavoriteEvent.objects.filter(user=request.user).values_list("event_id", flat=True)
        events = events.filter(id__in=favorite_event_ids)

    if show_past:
        events = events.filter(scheduled_at__lt=current_date)
    else:
        events = events.filter(scheduled_at__gte=current_date)

    events = events.order_by('scheduled_at')

    user_favorites = set(
        FavoriteEvent.objects.filter(user=request.user).values_list("event_id", flat=True)
    )

    return render(
        request,
        "app/events.html",
        {
            "events": events,
            "user_is_organizer": request.user.is_organizer,
            "user_favorites": user_favorites,
            "show_favorites": show_favorites,
            "user_id": request.user.id,
            "show_past": show_past,
        },
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    user_comments = Comment.objects.filter(event = event, user = request.user).exclude(isDeleted = True)
    other_comments = Comment.objects.filter(event = event, isDeleted=False).exclude(user = request.user)
    comments_count = user_comments.count() + other_comments.count()
    venue_capacity = event.venue_capacity if event.venue else 0
    tickets_percentage = event.tickets_percentage if venue_capacity else 0

    return render(request, "app/event_detail.html", {"event": event, "user_comments": user_comments, "other_comments": other_comments, "comments_count": comments_count, "user_is_organizer": request.user.is_organizer, "tickets_count": event.ticket_count, "venue_capacity": venue_capacity, "tickets_percentage": tickets_percentage})


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
        venue = get_object_or_404(Venue, pk=request.POST.get("venue"))

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.new(title, description, scheduled_at, request.user, category, venue)
        else:
            event = get_object_or_404(Event, pk=id)
            state=request.POST.get("state")
            print(state)
            event.update(title, description, scheduled_at, request.user, category, venue,state)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    categories = Category.objects.filter(is_active=True)
    venues = Venue.objects.filter(isDeleted=False)

    return render(
        request,
        "app/event_form.html",
        {
            "event": event,
            "user_is_organizer": request.user.is_organizer,
            "categories": categories,
            "venues": venues,
        },
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

        errors = Notification.validate_notification(
            title=title,
            message=message,
            event_id=event_id if event_id else None,
            recipients_type=recipients_type if not is_edit else None,
            user_id=user_id if not is_edit else None
        )

        if errors:
            for error_msg in errors.values():
                messages.error(request, error_msg)
            return render(request, 'app/notifications_form.html', {
                'notification': notification,
                'is_edit': is_edit,
                'events': Event.objects.all(),
                'users': User.objects.all(),
                'form_data': request.POST,
            })

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

    # Inicializar form_data vacío para la primera carga
    form_data = {}
    if notification:
        form_data = {
            'title': notification.title,
            'message': notification.message,
            'priority': notification.priority,
        }
        if notification.event:
            form_data['event'] = notification.event.id

    return render(request, 'app/notifications_form.html', {
        'notification': notification,
        'is_edit': is_edit,
        'events': Event.objects.all(),
        'users': User.objects.all(),
        'form_data': form_data,
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

@login_required
def ticket_form(request,id=None):
    ticket = {}
    events = Event.objects.exclude(state="FINALIZADO")
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

        # Validación de máximo 4 entradas por usuario y evento
        entradas_existentes = Ticket.objects.filter(event=event, user=user, is_deleted=False)
        total_entradas = sum(t.quantity for t in entradas_existentes)
        if total_entradas + quantity > 4:
            return render(request, 'app/ticket_form.html', {
                "events": events,
                "ticket": ticket,
                "error": "No puedes comprar más de 4 entradas para este evento. Ya tienes {} y estás intentando comprar {}.".format(total_entradas, quantity)
            })

        

        if not hay_cupo_disponible(event, quantity):
            return render(request, 'app/ticket_form.html', {
                "events": events,
                "ticket": ticket,
                "error": "No hay suficiente cupo disponible para este evento."
        })


        if id is None:
            Ticket.new(tipo_ticket,event,user,quantity)
            event.update_state_if_sold_out()
            return redirect("tickets")
        Ticket.update_ticket(id, tipo_ticket, event,quantity=quantity)

        
        return redirect("tickets")
    return render(request, "app/ticket_form.html", {"events":events,"ticket":ticket})


def hay_cupo_disponible(event, cantidad):
    if event.venue is None:
        return False
    return event.total_tickets_sold() + cantidad <= event.venue.capacity


def ticket_delete(request, id):
    if request.method == "POST":
        ticket = get_object_or_404(Ticket, pk=id)
        event = ticket.event
        Ticket.delete_ticket(id)
        event.update_state_if_sold_out()
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

        validation_result = Venue.validate_data(name, address, city, capacity, contact)
        if isinstance(validation_result, dict) and 'name' in validation_result and 'address' in validation_result:
            venue = Venue.objects.create(**validation_result)
            return redirect('list_venues')
        else:
            return render(request, 'app/venue_form.html', {'errors': validation_result, 'data': request.POST})

    return render(request, 'app/venue_form.html')

@login_required
def edit_venue(request, id):
    venue = get_object_or_404(Venue, id=id)

    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        capacity = request.POST.get('capacity')
        contact = request.POST.get('contact')

        errors_or_data = Venue.validate_data(name, address, city, capacity, contact)
        
        if isinstance(errors_or_data, dict) and any(k in ['name', 'address', 'city', 'capacity', 'contact'] for k in errors_or_data):
            return render(request, 'app/venue_edit.html', {'venue': venue, 'errors': errors_or_data})

        for attr, value in errors_or_data.items():
            setattr(venue, attr, value)
        venue.save()
        return redirect('list_venues')

    return render(request, 'app/venue_edit.html', {'venue': venue})


@login_required
def delete_venue(request, id):
    venue = get_object_or_404(Venue, id=id)
    
    if request.method == 'POST':
        venue.isDeleted = True
        venue.delete()
        return redirect('list_venues')

    return render(request, 'app/venue_confirm_delete.html', {'venue': venue})

@login_required
def venue_detail(request, venue_id):
    venue = get_object_or_404(Venue, pk=venue_id)
    return render(request, 'app/venue_detail.html', {'venue': venue})

@login_required
def toggle_favorite(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    favorite, created = FavoriteEvent.objects.get_or_create(user=request.user, event=event)

    if not created:
        favorite.delete()
        messages.success(request, "Evento eliminado de tus favoritos.")
    else:
        messages.success(request, "Evento agregado a tus favoritos.")

    next_url = request.POST.get('next') or request.GET.get('next') or request.META.get('HTTP_REFERER') or '/events/'
    return redirect(next_url)



