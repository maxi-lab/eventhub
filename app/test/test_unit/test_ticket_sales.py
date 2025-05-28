from django.test import TestCase
from app.models import Event, Venue, Ticket, User
from django.utils import timezone
import datetime

class TicketSalesPercentageTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword", is_organizer=True)
        self.venue = Venue.objects.create(name="Test Venue", capacity=100)
        self.event = Event.objects.create(
            title="Test Event",
            venue=self.venue,
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.user)

    def test_tickets_count_and_percentage_calculation(self):
        #Para 0 entradas vendidas
        self.assertEqual(self.event.ticket_count, 0, "La cantidad de entradas del evento no es 0")
        self.assertEqual(self.event.tickets_percentage, 0.0, "El porcentage de entradas del evento no es 0")

        #Crear 45 entradas para el evento
        Ticket.objects.create(event=self.event, user=self.user, quantity=45)
        self.assertEqual(self.event.ticket_count, 45, "La cantidad de entradas del evento no coincide con el esperado")
        self.assertEqual(self.event.tickets_percentage, 45.0, "El porcentaje de entradas del evento no coincide con el esperado")

        #Crear 5 entradas por separado
        for i in range(5):
            Ticket.objects.create(event=self.event, user=self.user)
        self.assertEqual(self.event.ticket_count, 50, "La cantidad de entradas del evento no coincide con el esperado")
        self.assertEqual(self.event.tickets_percentage, 50.0, "El porcentaje de entradas del evento no coincide con el esperado")
