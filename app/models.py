from django.contrib.auth.models import AbstractUser
from django.db import models


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


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    def new(cls, title, description, scheduled_at, organizer):
        errors = Event.validate(title, description, scheduled_at)

        if len(errors.keys()) > 0:
            return False, errors

        Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
        )

        return True, None

    def update(self, title, description, scheduled_at, organizer):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer

        self.save()

class Ticket(models.Model):
    price=models.DecimalField(max_digits=10, decimal_places=2)
    buy_date=models.DateTimeField(auto_now_add=True) 
    type_ticket=models.CharField(max_length=50)
    status=models.CharField(max_length=50, default="active")
    event=models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    is_deleted=models.BooleanField(default=False)
    quantity=models.IntegerField(default=1)
    def __str__(self):
        return f"{self.type_ticket} - {self.event.title} - {self.user.username}"
    @classmethod
    def new(cls, price, type_ticket, event, user,quantity):
        errors = {}
        if price <= 0:
            errors["price"] = "El precio debe ser mayor a 0"
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
        
        Ticket.objects.create(
        price=price,
        type_ticket=type_ticket,
        event=event,
        user=user,
        quantity=quantity
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
    def update_ticket(cls, ticket_id, price=None, type_ticket=None, event=None, user=None, quantity=None):
        try:
            ticket = Ticket.objects.get(id=ticket_id)
            if quantity is not None and quantity >= 0:
                ticket.quantity = quantity
            if price is not None:
                ticket.price = price
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
        
