import datetime
import re

from django.utils import timezone
from playwright.sync_api import expect

from app.models import Event, User, Category, Venue

from app.test.test_e2e.base import BaseE2ETest


class BuyTicketsBaseTest(BaseE2ETest):
    """Clase base específica para tests de compra de tickets"""

    def setUp(self):
        super().setUp()

        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@example.com",
            password="password123",
            is_organizer=True
        )
        self.category=Category.objects.create(
            name="Test",
            description="Test Category"
        )
        self.venue=Venue.objects.create(
            name="Test",
            address="Test",
            city="Test",
            capacity=100,
            contact="test"
        )
        # Crear usuario regular
        self.regular_user = User.objects.create_user(
            username="usuario",
            email="usuario@example.com",
            password="password123",
            is_organizer=False,
        )

        # Crear eventos de prueba
        # Evento 1
        event_date1 = timezone.make_aware(datetime.datetime(2025, 6, 10, 10, 10))
        self.event1 = Event.objects.create(
            title="Evento de prueba 1",
            description="Descripción del evento 1",
            scheduled_at=event_date1,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category,
            state="FINALIZADO"
        )

        # Evento 2
        event_date2 = timezone.make_aware(datetime.datetime(2025, 7, 15, 14, 30))
        self.event2 = Event.objects.create(
            title="Evento de prueba 2",
            description="Descripción del evento 2",
            scheduled_at=event_date2,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category
        )
        self.category2=Category.objects.create(
            name="Test2",
            description="Test Category"
        )
        self.venue2=Venue.objects.create(
            name="Test2",
            address="Test",
            city="Test",
            capacity=100,
            contact="test"
        )

class BuyTicketUnfinishTest(BuyTicketsBaseTest):
    """Test relacionado a la compra de tickets"""
    def test_buy_not_fished_event_ticket(self):
        self.login_user("usuario","password123")
        self.page.goto(f"{self.live_server_url}/tickets/create/")
        events=self.page.get_by_label("Evento").locator("option")
        expect(events).to_have_count(1)