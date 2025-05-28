import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from app.models import User, Event, Category, Venue, Ticket

class TestTicketLimitIntegration(TestCase):
    def setUp(self):
        self.client = Client()
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

    def login(self):
        self.client.login(username="comprador", password="testpass123")

    def test_limite_4_entradas_por_evento(self):
        self.login()
        url = reverse("ticket_form")
        # Compra inicial de 2 entradas
        resp = self.client.post(url, {
            "type_ticket": "GRL",
            "event_id": self.event.id,
            "quantity": 2,
            "card_number": "1234567890123456",
            "expiration_date": "12/30",
            "cvv": "123",
            "cardholder_name": "Test User"
        })
        self.assertEqual(resp.status_code, 302)  # Redirige a tickets
        # Compra adicional de 2 entradas (total 4)
        resp = self.client.post(url, {
            "type_ticket": "GRL",
            "event_id": self.event.id,
            "quantity": 2,
            "card_number": "1234567890123456",
            "expiration_date": "12/30",
            "cvv": "123",
            "cardholder_name": "Test User"
        })
        self.assertEqual(resp.status_code, 302)
        # Intento de comprar 1 entrada más (debe mostrar error)
        resp = self.client.post(url, {
            "type_ticket": "GRL",
            "event_id": self.event.id,
            "quantity": 1,
            "card_number": "1234567890123456",
            "expiration_date": "12/30",
            "cvv": "123",
            "cardholder_name": "Test User"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No puedes comprar más de 4 entradas para este evento")
        # Verifica que el total de entradas es 4
        tickets = Ticket.objects.filter(event=self.event, user=self.user, is_deleted=False)
        self.assertEqual(sum(t.quantity for t in tickets), 4)

    def test_limite_independiente_por_evento(self):
        self.login()
        url = reverse("ticket_form")
        # Compra 4 entradas para el primer evento
        resp = self.client.post(url, {
            "type_ticket": "GRL",
            "event_id": self.event.id,
            "quantity": 4,
            "card_number": "1234567890123456",
            "expiration_date": "12/30",
            "cvv": "123",
            "cardholder_name": "Test User"
        })
        self.assertEqual(resp.status_code, 302)
        # Crear otro evento
        event2 = Event.objects.create(
            title="Evento Test 2",
            description="Descripción 2",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )
        # Puede comprar 4 entradas para el otro evento
        resp = self.client.post(url, {
            "type_ticket": "GRL",
            "event_id": event2.id,
            "quantity": 4,
            "card_number": "1234567890123456",
            "expiration_date": "12/30",
            "cvv": "123",
            "cardholder_name": "Test User"
        })
        self.assertEqual(resp.status_code, 302)
        tickets1 = Ticket.objects.filter(event=self.event, user=self.user, is_deleted=False)
        tickets2 = Ticket.objects.filter(event=event2, user=self.user, is_deleted=False)
        self.assertEqual(sum(t.quantity for t in tickets1), 4)
        self.assertEqual(sum(t.quantity for t in tickets2), 4)
