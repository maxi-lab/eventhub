from django.test import TestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from app.models import Event, Venue, Category, Ticket
from django.utils import timezone
from datetime import timedelta

class TicketFunctionalityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.venue = Venue.objects.create(
            name="Test Venue",
            address="123 Street",
            city="City",
            capacity=100,
            contact="123456"
        )
        self.category = Category.objects.create(
            name="Test Category",
            description="Category Desc"
        )
        self.event = Event.objects.create(
            title="Test Event",
            description="Description",
            scheduled_at=timezone.now() + timedelta(days=5),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )

    def test_total_tickets_sold_initial(self):
        self.assertEqual(self.event.total_tickets_sold(), 0)

    def test_total_tickets_sold_after_purchase(self):
        Ticket.objects.create(
            type_ticket="GRL",
            event=self.event,
            user=self.user,
            quantity=10
        )
        self.assertEqual(self.event.total_tickets_sold(), 10)

    def test_hay_cupo_disponible_true(self):
        from app.views import hay_cupo_disponible
        self.assertTrue(hay_cupo_disponible(self.event, 10))

    def test_hay_cupo_disponible_false(self):
        from app.views import hay_cupo_disponible
        Ticket.objects.create(
            type_ticket="VIP",
            event=self.event,
            user=self.user,
            quantity=100
        )
        self.assertFalse(hay_cupo_disponible(self.event, 1))


    def test_update_state_if_sold_out_changes_state(self):
        # Estado inicial debe ser ACTIVO
        self.assertEqual(self.event.state, "ACTIVO")

        # Crear tickets para llenar la capacidad total del venue
        Ticket.objects.create(
            type_ticket="VIP",
            event=self.event,
            user=self.user,
            quantity=self.venue.capacity  # llena el cupo
        )

        # Ejecutar método para actualizar estado
        self.event.update_state_if_sold_out()

        # Recargar desde la base de datos
        self.event.refresh_from_db()

        # Verificar que el estado cambió a AGOTADO
        self.assertEqual(self.event.state, "AGOTADO")

        # Eliminar tickets para simular disponibilidad
        Ticket.objects.all().delete()

        # Ejecutar método para actualizar estado de nuevo
        self.event.update_state_if_sold_out()
        self.event.refresh_from_db()

        # Verificar que el estado volvió a ACTIVO
        self.assertEqual(self.event.state, "ACTIVO")    
