import datetime
import time

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Event, User, Category, Venue

class BaseEventTestCase(TestCase):
    """Clase base con la configuración común para todos los tests de eventos"""

    def setUp(self):
        # Crear un usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        # Crear un usuario regular
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@test.com",
            password="password123",
            is_organizer=False,
        )

        # Crear algunos eventos de prueba
        self.event1 = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
        )

        self.event2 = Event.objects.create(
            title="Evento 2",
            description="Descripción del evento 2",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.organizer,
            state="FINALIZADO"
        )
        self.category=Category.objects.create(
            name="category_test",
            description="categoria de prueba"
        )
        self.venue=Venue.objects.create(
            name="Test",
            address="Test",
            city="Test",
            capacity=100,
            contact="Test"
        )
        self.category2=Category.objects.create(
            name="category_test2",
            description="categoria de prueba"
        )
        self.venue2=Venue.objects.create(
            name="Test2",
            address="Test",
            city="Test",
            capacity=100,
            contact="Test"
        )
        

        # Cliente para hacer peticiones
        self.client = Client()
class ListEventBuyTickets(BaseEventTestCase):
    """Test que verifica el listado de opciones de eventos para comprar ticket sean de un evento no finalizado"""
    def test_buy_tickets_sold_out(self):
        self.client.login(username="regular", password="password123")
        response = self.client.get(reverse("ticket_form"))
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response,"app/ticket_form.html")
        self.assertIn("events",response.context)
        events=list(response.context["events"])
        self.assertEqual(len(events),1)
