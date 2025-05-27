import datetime

from django.utils import timezone
from playwright.sync_api import expect

from app.models import Event, User, Category, Venue
from app.test.test_e2e.base import BaseE2ETest


class FavoriteEventsE2ETest(BaseE2ETest):
    """Tests E2E para la funcionalidad de favoritos en eventos"""

    def setUp(self):
        super().setUp()

        self.user = User.objects.create_user(
            username="usuario123",
            email="usuario@xd.com",
            password="usuario123",
            is_organizer=False,
        )

        self.category = Category.objects.create(name="Test", description="Test Category")
        self.venue = Venue.objects.create(
            name="Venue123",
            address="Messi 123",
            city="Ciudad123",
            capacity=100,
            contact="contacto123@xd.com"
        )

        event_date1 = timezone.make_aware(datetime.datetime(2025, 6, 10, 10, 0))
        event_date2 = timezone.make_aware(datetime.datetime(2025, 7, 10, 12, 0))

        self.event1 = Event.objects.create(
            title="Evento Favorito 1",
            description="Descripción del evento favorito 1",
            scheduled_at=event_date1,
            organizer=self.user,
            venue=self.venue,
            category=self.category,
        )

        self.event2 = Event.objects.create(
            title="Evento Favorito 2",
            description="Descripción del evento favorito 2",
            scheduled_at=event_date2,
            organizer=self.user,
            venue=self.venue,
            category=self.category,
        )

    def test_mark_unmark_favorite_and_filter(self):
        """Marcar, desmarcar favoritos y verificar el filtrado manual con URL"""
        self.login_user("usuario123", "usuario123")
        self.page.goto(f"{self.live_server_url}/events/")

        expect(self.page.get_by_text("Evento Favorito 1", exact=True)).to_be_visible()
        expect(self.page.get_by_text("Evento Favorito 2", exact=True)).to_be_visible()

        star_buttons = self.page.locator("button[title='Favorito']")
        expect(star_buttons).to_have_count(2)
        expect(star_buttons.nth(0).locator("i.bi-star")).to_be_visible()
        expect(star_buttons.nth(1).locator("i.bi-star")).to_be_visible()

        star_buttons.nth(0).click()
        self.page.wait_for_load_state("networkidle")
        expect(star_buttons.nth(0).locator("i.bi-star-fill")).to_be_visible()
        expect(star_buttons.nth(1).locator("i.bi-star")).to_be_visible()

        self.page.goto(f"{self.live_server_url}/events/?favorites=1")
        expect(self.page.get_by_text("Evento Favorito 1", exact=True)).to_be_visible()
        expect(self.page.get_by_text("Evento Favorito 2", exact=True)).not_to_be_visible()

        star_buttons = self.page.locator("button[title='Favorito']")
        star_buttons.nth(0).click()
        self.page.wait_for_load_state("networkidle")

        expect(self.page.locator("text=No hay eventos disponibles")).to_be_visible()

        self.page.goto(f"{self.live_server_url}/events/")
        expect(self.page.get_by_text("Evento Favorito 1", exact=True)).to_be_visible()
        expect(self.page.get_by_text("Evento Favorito 2", exact=True)).to_be_visible()
        star_buttons = self.page.locator("button[title='Favorito']")
        expect(star_buttons.nth(0).locator("i.bi-star")).to_be_visible()
        expect(star_buttons.nth(1).locator("i.bi-star")).to_be_visible()

    def test_filter_buttons_work(self):
        """Verifica que los botones 'Solo Favoritos' y 'Ver Todos' funcionen correctamente"""
        self.login_user("usuario123", "usuario123")
        self.page.goto(f"{self.live_server_url}/events/")

        expect(self.page.get_by_text("Evento Favorito 1", exact=True)).to_be_visible()
        expect(self.page.get_by_text("Evento Favorito 2", exact=True)).to_be_visible()

        star_buttons = self.page.locator("button[title='Favorito']")
        star_buttons.nth(0).click()
        self.page.wait_for_load_state("networkidle")

        self.page.locator("a:has-text('Solo Favoritos')").click()
        self.page.wait_for_url("**/events/?favorites=1")
        expect(self.page.get_by_text("Evento Favorito 1", exact=True)).to_be_visible()
        expect(self.page.get_by_text("Evento Favorito 2", exact=True)).not_to_be_visible()

        self.page.locator("a:has-text('Ver Todos')").click()
        self.page.wait_for_url("**/events/")
        expect(self.page.get_by_text("Evento Favorito 1", exact=True)).to_be_visible()
        expect(self.page.get_by_text("Evento Favorito 2", exact=True)).to_be_visible()
