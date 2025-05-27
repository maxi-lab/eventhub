from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import datetime
from app.models import Event, User, Category, Venue

class EventsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
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
            title='Evento Pasado Test',
            description='Descripción del evento pasado',
            scheduled_at=self.now - datetime.timedelta(days=1),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )
        
        # Evento futuro
        self.future_event = Event.objects.create(
            title='Evento Futuro Test',
            description='Descripción del evento futuro',
            scheduled_at=self.now + datetime.timedelta(days=1),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )
        
        # Login
        self.client.login(username='testuser', password='testpass123')

    def test_events_view_shows_future_events_by_default(self):
        """Test que verifica que por defecto se muestran los eventos futuros"""
        response = self.client.get(reverse('events'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Evento Futuro Test')
        self.assertNotContains(response, 'Evento Pasado Test')

    def test_events_view_shows_past_events_with_parameter(self):
        """Test que verifica que se muestran los eventos pasados con el parámetro show_past"""
        response = self.client.get(reverse('events') + '?show_past=true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Evento Pasado Test')
        self.assertNotContains(response, 'Evento Futuro Test')

    def test_events_view_requires_login(self):
        """Test que verifica que la vista requiere login"""
        self.client.logout()
        response = self.client.get(reverse('events'))
        self.assertEqual(response.status_code, 302)  # Redirección al login 