import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from app.models import User, Event, Category, Venue, FavoriteEvent

class FavoriteEventViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Crear usuario y loguearlo
        self.user = User.objects.create_user(
            username='usuario123',
            email='usuario@xd.com',
            password='usuario123'
        )
        self.client.login(username='usuario123', password='usuario123')

        # Crear categoría y venue
        self.category = Category.objects.create(
            name='Categoria123',
            description='Buena Categoria'
        )
        self.venue = Venue.objects.create(
            name='Venue123',
            address='Messi 123',
            city='Ciudad',
            capacity=100,
            contact='Contacto123'
        )

        # Crear evento
        self.event = Event.objects.create(
            title='Evento Favorito Test',
            description='Descripción del evento favorito',
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )

    def test_user_can_add_event_to_favorites_from_view(self):
        """Test que verifica que un usuario puede agregar un evento a favoritos desde la vista"""
        response = self.client.post(reverse('toggle_favorite', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.user.favorite_events.filter(pk=self.event.id).exists())

    def test_user_can_remove_event_from_favorites_from_view(self):
        """Test que verifica que un usuario puede quitar un evento de favoritos desde la vista"""
        FavoriteEvent.objects.create(user=self.user, event=self.event)  
        response = self.client.post(reverse('toggle_favorite', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(FavoriteEvent.objects.filter(user=self.user, event=self.event).exists())

    def test_events_view_shows_only_favorite_events_with_param(self):
        """Test que verifica que se muestran solo los eventos favoritos al pasar ?favorites=1"""
        FavoriteEvent.objects.create(user=self.user, event=self.event)  
        response = self.client.get(reverse('events') + '?favorites=1')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)

