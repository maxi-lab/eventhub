import datetime
from django.utils import timezone
from playwright.sync_api import expect
from app.models import User, Event, Category, Venue
from app.test.test_e2e.base import BaseE2ETest

class TestTicketLimitE2E(BaseE2ETest):
    def setUp(self):
        super().setUp()
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

    def test_limite_4_entradas_e2e(self):
        # Login
        self.page.goto(f"{self.live_server_url}/accounts/login/")
        self.page.get_by_label("Usuario").fill("comprador")
        self.page.get_by_label("Contraseña").fill("testpass123")
        self.page.get_by_role("button", name="Iniciar sesión").click()
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        # Comprar 2 entradas
        self.page.goto(f"{self.live_server_url}/tickets/create/")
        self.page.get_by_label("Cantidad de Entradas").fill("2")
        self.page.locator('input[type="radio"][name="type_ticket"][value="GRL"]').check()
        self.page.get_by_label("Evento").select_option(label="Evento Test")
        self.page.locator('#card_number').fill("1234567890123456")
        self.page.locator('#expiration_date').fill("12/30")
        self.page.locator('#cvv').fill("123")
        self.page.locator('#cardholder_name').fill("Test User")
        self.page.locator('input[type="checkbox"]').check()
        self.page.get_by_role("button", name="Confirmar Compra").click()
        expect(self.page).to_have_url(f"{self.live_server_url}/tickets/")

        # Comprar 2 entradas más
        self.page.goto(f"{self.live_server_url}/tickets/create/")
        self.page.get_by_label("Cantidad de Entradas").fill("2")
        self.page.locator('input[type="radio"][name="type_ticket"][value="GRL"]').check()
        self.page.get_by_label("Evento").select_option(label="Evento Test")
        self.page.locator('#card_number').fill("1234567890123456")
        self.page.locator('#expiration_date').fill("12/30")
        self.page.locator('#cvv').fill("123")
        self.page.locator('#cardholder_name').fill("Test User")
        self.page.locator('input[type="checkbox"]').check()
        self.page.get_by_role("button", name="Confirmar Compra").click()
        expect(self.page).to_have_url(f"{self.live_server_url}/tickets/")

        # Intentar comprar 1 entrada más (debe mostrar error)
        self.page.goto(f"{self.live_server_url}/tickets/create/")
        self.page.get_by_label("Cantidad de Entradas").fill("1")
        self.page.locator('input[type="radio"][name="type_ticket"][value="GRL"]').check()
        self.page.get_by_label("Evento").select_option(label="Evento Test")
        self.page.locator('#card_number').fill("1234567890123456")
        self.page.locator('#expiration_date').fill("12/30")
        self.page.locator('#cvv').fill("123")
        self.page.locator('#cardholder_name').fill("Test User")
        self.page.locator('input[type="checkbox"]').check()
        self.page.get_by_role("button", name="Confirmar Compra").click()
        expect(self.page).to_have_url(f"{self.live_server_url}/tickets/create/")
        expect(self.page.get_by_text("No puedes comprar más de 4 entradas para este evento")).to_be_visible()
