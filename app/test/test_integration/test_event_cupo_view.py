from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from app.models import Event, Venue, Category, Ticket
from django.contrib.auth import get_user_model

User = get_user_model()

class TicketIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

        self.venue = Venue.objects.create(
            name="Venue 1",
            address="Address 1",
            city="City",
            capacity=5,  # capacidad pequeña para probar agotamiento rápido
            contact="123456"
        )
        self.category = Category.objects.create(
            name="Category 1",
            description="Desc"
        )
        self.event = Event.objects.create(
            title="Evento Test",
            description="Desc",
            scheduled_at=timezone.now() + timedelta(days=3),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )

    def test_integrated_ticket_purchase_and_sold_out(self):
        # 1. Comprar tickets dentro del límite
        response = self.client.post(reverse('ticket_form'), {
            'type_ticket': 'GRL',
            'event_id': self.event.id,
            'quantity': 3,
            'card_number': '1234567890123456',
            'expiration_date': '12/25',
            'cvv': '123',
            'cardholder_name': 'Test User',
            # checkbox (aceptar términos) simulación
        }, follow=True)
        self.assertRedirects(response, reverse('tickets'))
        self.event.refresh_from_db()
        self.assertEqual(self.event.state, 'ACTIVO')
        self.assertEqual(self.event.total_tickets_sold(), 3)

        # 2. Intentar comprar más tickets que el cupo restante (2 disponibles)
        response = self.client.post(reverse('ticket_form'), {
            'type_ticket': 'GRL',
            'event_id': self.event.id,
            'quantity': 3,  # 3 > 2 restantes
            'card_number': '1234567890123456',
            'expiration_date': '12/25',
            'cvv': '123',
            'cardholder_name': 'Test User',
        })
        self.assertContains(response, "No hay suficiente cupo disponible para este evento.")

        # 3. Comprar tickets para agotar el cupo restante (2 tickets)
        response = self.client.post(reverse('ticket_form'), {
            'type_ticket': 'GRL',
            'event_id': self.event.id,
            'quantity': 2,
            'card_number': '1234567890123456',
            'expiration_date': '12/25',
            'cvv': '123',
            'cardholder_name': 'Test User',
        }, follow=True)
        self.assertRedirects(response, reverse('tickets'))
        self.event.refresh_from_db()
        self.assertEqual(self.event.state, 'AGOTADO')
        self.assertEqual(self.event.total_tickets_sold(), 5)

        # 4. Verificar que el evento agotado no aparece como opción seleccionable (GET en formulario)
        response = self.client.get(reverse('ticket_form'))
        self.assertContains(response, f'{self.event.title} - AGOTADO')
        # Opciones agotadas deben estar deshabilitadas en el select
        self.assertContains(response, 'disabled')

