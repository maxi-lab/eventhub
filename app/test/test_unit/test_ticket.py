import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from app.models import Event, Ticket, Category, Venue
from django.utils import timezone

User = get_user_model()

class TicketLimitTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="comprador",
            email="comprador@test.com",
            password="testpass123",
            is_organizer=False
        )
        self.category = Category.objects.create(
            name="Test Category",
            description="Test Description"
        )
        self.venue = Venue.objects.create(
            name="Test Venue",
            address="Test Address",
            city="Test City",
            capacity=100,
            contact="Test Contact"
        )
        self.event = Event.objects.create(
            title="Evento Test",
            description="Descripción",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )

    def test_usuario_puede_comprar_hasta_4_entradas(self):
        ok, err = Ticket.new("GRL", self.event, self.user, 2)
        self.assertTrue(ok)
        ok, err = Ticket.new("GRL", self.event, self.user, 2)
        self.assertTrue(ok)
        ok, err = Ticket.new("GRL", self.event, self.user, 1)
        self.assertFalse(ok)
        self.assertTrue(err is not None and "max_tickets" in err, f"Error esperado en err, recibido: {err}")

    def test_usuario_no_puede_superar_limite_con_una_compra(self):
        ok, err = Ticket.new("GRL", self.event, self.user, 4)
        self.assertTrue(ok)
        ok, err = Ticket.new("GRL", self.event, self.user, 1)
        self.assertFalse(ok)
        self.assertTrue(err is not None and "max_tickets" in err, f"Error esperado en err, recibido: {err}")

    def test_usuario_puede_comprar_4_por_evento_distinto(self):
        ok, err = Ticket.new("GRL", self.event, self.user, 4)
        self.assertTrue(ok)
        event2 = Event.objects.create(
            title="Evento Test 2",
            description="Descripción 2",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )
        ok, err = Ticket.new("GRL", event2, self.user, 4)
        self.assertTrue(ok)
        ok, err = Ticket.new("GRL", event2, self.user, 1)
        self.assertFalse(ok)
        self.assertTrue(err is not None and "max_tickets" in err, f"Error esperado en err, recibido: {err}")
