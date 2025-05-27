from django.contrib.auth import get_user_model
from app.models import Venue, Event, Ticket, User
from django.utils import timezone
from datetime import datetime, timedelta
from playwright.sync_api import expect
from app.test.test_e2e.base import BaseE2ETest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import sync_playwright

class TicketSaleBaseEvent(StaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

         # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

        self.venue = Venue.objects.create(
            name="testvenue",
            capacity=100
        )
            
    def test_ticket_percentage_display(self):
        # Crear usuario y evento
        User = get_user_model()
        user = User.objects.create_user(username="testuser", password="1234", is_organizer=True)
        event = Event.objects.create(
            title="Evento Test",
            description="Descripción de prueba",
            venue=self.venue,
            organizer=user,
            scheduled_at=datetime.now() + timedelta(days=1)
        )
        Ticket.objects.create(event=event, quantity=8, user=self.organizer)

        # Ir a la página de login
        self.page.goto(f"{self.live_server_url}/accounts/login/")

        # Completar y enviar formulario de login
        self.page.fill('input[name="username"]', self.organizer.username)
        self.page.fill('input[name="password"]', "password123")
        self.page.click('button[type="submit"]')
        self.page.wait_for_url(f"{self.live_server_url}/events/")

        # Navegar a la página del detalle del evento
        event_detail_url = f"{self.live_server_url}/events/{event.id}/"
        self.page.goto(event_detail_url)

        # Verificar texto esperado
        locator = self.page.locator(".card-text", has_text="Entradas vendidas")
        locator.wait_for(state="visible", timeout=5000)
        expect(locator).to_contain_text("Entradas vendidas: 8 de 100")

        locatoralert = self.page.locator(".alert.alert-danger")
        locatoralert.wait_for(state="visible", timeout=5000)
        expect(locatoralert).to_contain_text("Baja demanda. Solo 8,0% de entradas vendidas.")