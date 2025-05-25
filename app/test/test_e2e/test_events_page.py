import pytest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone
from django.test import Client
import datetime
from playwright.sync_api import sync_playwright, expect
from app.models import Event, User, Category, Venue
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY

class EventsE2ETest(StaticLiveServerTestCase):
    def setUp(self):
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Crear categoría y venue
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description'
        )
        self.venue = Venue.objects.create(
            name='Test Venue',
            address='Test Address',
            city='Test City',
            capacity=100,
            contact='Test Contact'
        )
        
        # Crear eventos de prueba
        self.now = timezone.now()
        
        # Evento pasado
        self.past_event = Event.objects.create(
            title='Evento Pasado E2E',
            description='Descripción del evento pasado',
            scheduled_at=self.now - datetime.timedelta(days=1),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )
        
        # Evento futuro
        self.future_event = Event.objects.create(
            title='Evento Futuro E2E',
            description='Descripción del evento futuro',
            scheduled_at=self.now + datetime.timedelta(days=1),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )

        # Crear cliente y hacer login
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_event_filtering_workflow(self):
        """Test end-to-end del flujo de filtrado de eventos"""
        # Verificar que por defecto se muestran los eventos futuros
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Evento Futuro E2E')
        self.assertNotContains(response, 'Evento Pasado E2E')

        # Verificar que se muestran los eventos pasados con el parámetro
        response = self.client.get('/events/?show_past=true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Evento Pasado E2E')
        self.assertNotContains(response, 'Evento Futuro E2E')

        # Verificar que se vuelven a mostrar los eventos futuros
        response = self.client.get('/events/?show_past=false')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Evento Futuro E2E')
        self.assertNotContains(response, 'Evento Pasado E2E') 