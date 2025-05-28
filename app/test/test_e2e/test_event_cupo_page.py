import datetime
from django.utils import timezone
from playwright.sync_api import expect
from app.models import Event, User, Category, Venue, Ticket, EventState
from app.test.test_e2e.base import BaseE2ETest
import re
from django.db import models


class TestTicketPurchase(BaseE2ETest):
    def setUp(self):
        super().setUp()
        # Crear usuario comprador
        self.buyer = User.objects.create_user(
            username="usuario123",
            email="usuario@xd.com",
            password="12345678A",
            is_organizer=False
        )
        # Crear organizador
        self.organizer = User.objects.create_user(username="organizer", password="12345")
        # Categoría y venue
        self.category = Category.objects.create(name="Conciertos")
        self.venue = Venue.objects.create(name="Auditorio", capacity=3)

        # Evento agotado (3 tickets vendidos)
        self.sold_out_event = Event.objects.create(
            title="Evento Agotado",
            description="Evento sin cupo",
            scheduled_at=timezone.now() + datetime.timedelta(days=3),
            organizer=self.organizer,
            category=self.category,
            venue=self.venue,
            state=EventState.ACTIVE
        )
        Ticket.objects.create(type_ticket="GRL", event=self.sold_out_event, user=self.buyer, quantity=3)
        self.sold_out_event.update_state_if_sold_out()
        self.sold_out_event.refresh_from_db()

        # Evento activo disponible
        self.active_event = Event.objects.create(
            title="Evento Disponible",
            description="Evento con espacio",
            scheduled_at=timezone.now() + datetime.timedelta(days=7),
            organizer=self.organizer,
            category=self.category,
            venue=self.venue,
            state=EventState.ACTIVE
        )

    def login(self, username, password):
        self.page.goto(f"{self.live_server_url}/accounts/login/")
        self.page.fill("input[name='username']", username)
        self.page.fill("input[name='password']", password)
        self.page.click("button[type='submit']")
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

    def test_purchase_ticket_success_and_block_sold_out(self):
        self.login("usuario123", "12345678A")

        # Navegar al formulario de compra
        self.page.goto(f"{self.live_server_url}/tickets/create/")
        expect(self.page).to_have_url(f"{self.live_server_url}/tickets/create/")

        # Verificar que el evento agotado aparece como deshabilitado
        sold_out_option = self.page.locator(f"select[name='event_id'] option[value='{self.sold_out_event.id}']")
        expect(sold_out_option).to_have_attribute("disabled", "")
        expect(sold_out_option).to_have_text("Evento Agotado - AGOTADO")

        # Seleccionar el evento activo
        self.page.select_option("select[name='event_id']", str(self.active_event.id))
        self.page.fill("input[name='quantity']", "2")
        self.page.fill("input[name='card_number']", "4242424242424242")
        self.page.fill("input[name='expiration_date']", "12/30")
        self.page.fill("input[name='cvv']", "123")
        self.page.fill("input[name='cardholder_name']", "Maria Lopez")
        self.page.check("input[type='checkbox']")

        with self.page.expect_navigation():
            self.page.get_by_role("button", name="Confirmar Compra").click()

        # Confirmar redirección a lista de tickets
        expect(self.page).to_have_url(re.compile(f"{self.live_server_url}/tickets/?"))

        expect(self.page.locator("h1")).to_have_text("Tickets")

        # Confirmar ticket en base de datos
        ticket_exists = Ticket.objects.filter(user=self.buyer, event=self.active_event, quantity=2).exists()
        self.assertTrue(ticket_exists, "El ticket no fue creado correctamente.")

        # Confirmar que el evento sigue ACTIVO
        self.active_event.refresh_from_db()
        self.assertEqual(self.active_event.state, EventState.ACTIVE)

        self.page.goto(f"{self.live_server_url}/tickets/create/")

        self.page.select_option("select[name='event_id']", str(self.active_event.id))
        self.page.fill("input[name='quantity']", "2")
        self.page.fill("input[name='card_number']", "2345432675126435")
        self.page.fill("input[name='expiration_date']", "12/29")
        self.page.fill("input[name='cvv']", "323")
        self.page.fill("input[name='cardholder_name']", "Gustavo")
        self.page.check("input[type='checkbox']")

        with self.page.expect_navigation(timeout=3000) as navigation_info:
            self.page.get_by_role("button", name="Confirmar Compra").click()

        # Esperamos que siga en la misma página (porque no hay cupo)
        expect(self.page).to_have_url(f"{self.live_server_url}/tickets/create/")

        # Verifica que el número total de tickets no haya aumentado
        total_tickets = Ticket.objects.filter(user=self.buyer, event=self.active_event).aggregate(total=models.Sum("quantity"))["total"]
        self.assertEqual(total_tickets, 2, "Se crearon más tickets de los permitidos por la capacidad del evento.")

        # Verifica que el mensaje de error aparezca en la página
        error_locator = self.page.locator("text=No hay suficiente cupo disponible para este evento.")
        expect(error_locator).to_be_visible()

