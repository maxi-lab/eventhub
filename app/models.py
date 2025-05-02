from django.contrib.auth.models import AbstractUser
from django.db import models
import random
import string
from django.utils import timezone

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class User(AbstractUser):
    is_organizer = models.BooleanField(default=False)

    @classmethod
    def validate_new_user(cls, email, username, password, password_confirm):
        errors = {}

        if email is None:
            errors["email"] = "El email es requerido"
        elif User.objects.filter(email=email).exists():
            errors["email"] = "Ya existe un usuario con este email"

        if username is None:
            errors["username"] = "El username es requerido"
        elif User.objects.filter(username=username).exists():
            errors["username"] = "Ya existe un usuario con este nombre de usuario"

        if password is None or password_confirm is None:
            errors["password"] = "Las contraseñas son requeridas"
        elif password != password_confirm:
            errors["password"] = "Las contraseñas no coinciden"

        return errors

class Category(models.Model):
    name = models.CharField()
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    objects = ActiveManager()
    all_objects = models.Manager()

    def __str__(self) -> str:
        return self.name
        
    @classmethod
    def validate(cls, name, description, is_active):
        errors = {}

        if name == "":
            errors["name"] = "Por favor ingrese un nombre"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        return errors

    @classmethod
    def new(cls, name, description, is_active):
        errors = Category.validate(name, description, is_active)

        if len(errors.keys()) > 0:
            return False, errors

        Category.objects.create(
            name=name,
            description=description,
            is_active=is_active,
        )

        return True, None

    def update(self, name, description, is_active):
        self.name = name or self.name
        self.description = description or self.description
        self.is_active = is_active 

        self.save()

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save()

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, related_name="events")

    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, title, description, scheduled_at):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        return errors

    @classmethod
    def new(cls, title, description, scheduled_at, organizer, category):
        errors = Event.validate(title, description, scheduled_at)

        if len(errors.keys()) > 0:
            return False, errors

        Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
            category=category,
        )

        return True, None

    def update(self, title, description, scheduled_at, organizer, category):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer
        self.category = category or self.category

        self.save()


class Priority(models.TextChoices):
    HIGH = "HIGH", "Alta"
    MEDIUM = "MEDIUM", "Media"
    LOW = "LOW", "Baja"

class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted=models.BooleanField(default=False)
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    users = models.ManyToManyField(User, through='UserNotification', related_name="notifications")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)

class UserNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'notification')

class Ticket(models.Model):
    GENERAL="GRL"
    VIP="VIP"
    TICKET_TYPES=[
        (GENERAL, "General"),
        (VIP, "VIP"),
    ]
    buy_date=models.DateTimeField(auto_now_add=True) 
    type_ticket=models.CharField(max_length=3, choices=TICKET_TYPES, default=GENERAL)
    code=models.CharField(max_length=10)
    event=models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    is_deleted=models.BooleanField(default=False)
    quantity=models.IntegerField(default=1)
    def __str__(self):
        return f"{self.type_ticket} - {self.event.title} - {self.user.username}"
    @classmethod
    def new(cls, type_ticket, event, user,quantity):
        errors = {}
        if type_ticket == "":
            errors["type_ticket"] = "Por favor ingrese un tipo de ticket"
        if event is None:
            errors["event"] = "Por favor seleccione un evento"
        if user is None:
            errors["user"] = "Por favor seleccione un usuario"
        if quantity<=0:
            errors["quantity"]="Una cantidad positiva"
        
        
        if len(errors.keys()) > 0:
            return False, errors
        characters = string.ascii_letters + string.digits
        code = ''.join(random.choice(characters) for _ in range(10))
        
        Ticket.objects.create(
        type_ticket=type_ticket,
        event=event,
        user=user,
        quantity=quantity,
        code=code,
        )
        return True, None 
    @classmethod
    def delete_ticket(cls, ticket_id):
        try:
            ticket = Ticket.objects.get(id=ticket_id)
            ticket.is_deleted=True
            ticket.save()
            return True, None
        except Ticket.DoesNotExist:
            return False, {"ticket": "El ticket no existe"}
    @classmethod
    def update_ticket(cls, ticket_id, type_ticket=None, event=None, user=None, quantity=None):
        try:
            ticket = Ticket.objects.get(id=ticket_id)
            if quantity is not None and quantity >= 0:
                ticket.quantity = quantity
            if type_ticket is not None:
                ticket.type_ticket = type_ticket
            if event is not None:
                ticket.event = event
            if user is not None:
                ticket.user = user
            ticket.save()
            return True, None
        except Ticket.DoesNotExist:
            return False, {"ticket": "El ticket no existe"}
        

class RefundRequest(models.Model):
    ticket=models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="refund_requests")
    approval_date=models.DateTimeField(null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    reason=models.TextField()
    status=models.CharField(max_length=10, choices=[("PENDING", "Pendiente"), ("APPROVED", "Aprobada"), ("DENIED", "Denegada")], default="PENDING")
    is_deleted = models.BooleanField(default=False)

    @classmethod
    def create_request(cls, user, ticket_code, reason):
        errors = {}

        try:
            ticket = Ticket.objects.get(code=ticket_code, user=user)
        except Ticket.DoesNotExist:
            errors["ticket"] = "No se encontró un ticket con ese código para este usuario"
            return False, errors

        if reason.strip() == "":
            errors["reason"] = "Debe ingresar un motivo"
            return False, errors

        if cls.objects.filter(ticket=ticket, status="PENDING", is_deleted=False).exists():
            errors["ticket"] = "Ya existe una solicitud pendiente para este ticket"
            return False, errors


        cls.objects.create(ticket=ticket, reason=reason)
        return True, None
    
    @classmethod
    def edit_request(cls, user, request_id, new_reason):
        errors = {}

        try:
            request = cls.objects.get(id=request_id)
        except cls.DoesNotExist:
            errors["request"] = "La solicitud no existe"
            return False, errors

        if request.status != "PENDING":
            errors["status"] = "Solo se pueden editar solicitudes pendientes"
            return False, errors

        if new_reason.strip() == "":
            errors["reason"] = "El motivo no puede estar vacío"
            return False, errors

        request.reason = new_reason
        request.save()
        return True, None
    
    @classmethod
    def delete_request(cls, user, request_id):
        errors = {}

        try:
            request = cls.objects.get(id=request_id)
        except cls.DoesNotExist:
            errors["request"] = "La solicitud no existe"
            return False, errors

        if request.status != "PENDING":
            errors["status"] = "Solo se pueden eliminar solicitudes pendientes"
            return False, errors

        request.is_deleted = True
        request.save()
        return True, None

    
    def change_status(self, new_status, admin_user):
        errors = {}

        if not admin_user.is_organizer:
            errors["permission"] = "Solo un administrador puede cambiar el estado de la solicitud"
            return False, errors

        if self.status != "PENDING":
            errors["status"] = "La solicitud ya ha sido procesada"
            return False, errors

        self.status = new_status
        self.approval_date = timezone.now()
        self.save()
        return True, None

class Comment(models.Model):
    title = models.TextField(max_length=50)
    text = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="published_comments")
    isDeleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} by {self.user.username}"

    @classmethod
    def validate(cls, title, text, user_id, event_id):
        errors = {}
        if not title:
            errors ["title"] = "El título es requerido"
        if not text:
            errors ["text"] = "El cuerpo es requerido"
        if not User.objects.filter(id=user_id).exists():
            errors ["user"] = "El usuario no existe"
        if not Event.objects.filter(id=event_id).exists():
            errors ["event"] = "El evento no existe"
        return errors

    @classmethod
    def new(cls, title, text, user_id, event_id):
        errors=Comment.validate(title, text, user_id, event_id)

        if len(errors.keys()) > 0:
            return False, errors
        
        Comment.objects.create(
            title=title,
            text=text,
            user=User.objects.get(id = user_id),
            event=Event.objects.get(id = event_id),
        )
        return True, None
    
    def Update(self, title, text):
        self.title = title or self.title
        self.text = text or self.text
        self.save()
    
    def delete(self):
        self.isDeleted = True
        self.save()
    