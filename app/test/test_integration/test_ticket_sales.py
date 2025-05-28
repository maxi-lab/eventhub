from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from app.models import Event, Ticket, Venue
from datetime import datetime, timedelta
from django.utils import timezone

class TicketSalesIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        User=get_user_model()
        self.user = User.objects.create_user(username='testuser', password='testpassword', is_organizer=True)
        self.client.login(username="testuser", password="testpassword")
        self.venue = Venue.objects.create(name='Test Venue', address='123', capacity=100)
        self.event = Event.objects.create(
            title='Integration Test Event',
            scheduled_at=timezone.now() + timedelta(days=1),
            venue=self.venue,
            organizer=self.user
        )
        # Crear 50 tickets
        for i in range(50):
            Ticket.objects.create(event=self.event, user=self.user)

    def test_event_detail_shows_correct_ticket_percentage(self):
        url = reverse('event_detail', args=[self.event.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200, "Redireccion inesperada")
        self.assertContains(response, "Entradas vendidas: 50 de 100", msg_prefix="Event detail no muestra la cantidad de tickets correctamente")

class LowDemandTest(TestCase):
    def setUp(self):
        self.client = Client()
        User=get_user_model()
        self.user = User.objects.create_user(username='testuser', password='testpassword', is_organizer=True)
        self.client.login(username="testuser", password="testpassword")
        self.venue = Venue.objects.create(name='Test Venue', address='123', capacity=100)
        self.event = Event.objects.create(
            title='Integration Test Event',
            scheduled_at=timezone.now() + timedelta(days=1),
            venue=self.venue,
            organizer=self.user
        )
        # Crear 5 tickets
        for i in range(5):
            Ticket.objects.create(event=self.event, user=self.user)

    def test_event_detail_shows_low_demand_message(self):
        url = reverse('event_detail', args=[self.event.pk])
        response = self.client.get(url)
        self.assertContains(response, "Baja demanda. Solo 5,0% de entradas vendidas.", msg_prefix="La alerta de baja demanda no se muestra correctamente")

class HighDemandTest(TestCase):
    def setUp(self):
        self.client = Client()
        User=get_user_model()
        self.user = User.objects.create_user(username='testuser', password='testpassword', is_organizer=True)
        self.client.login(username="testuser", password="testpassword")
        self.venue = Venue.objects.create(name='Test Venue', address='123', capacity=100)
        self.event = Event.objects.create(
            title='Integration Test Event',
            scheduled_at=timezone.now() + timedelta(days=1),
            venue=self.venue,
            organizer=self.user
        )
        # Crear 95 tickets
        for i in range(95):
            Ticket.objects.create(event=self.event, user=self.user)

    def test_event_detail_shows_high_demand_message(self):
        url = reverse('event_detail', args=[self.event.pk])
        response = self.client.get(url)
        self.assertContains(response, "Alta demanda. 95,0% de entradas vendidas.", msg_prefix="La alerta de alta demanda no se muestra correctamente")