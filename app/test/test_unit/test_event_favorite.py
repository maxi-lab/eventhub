from django.test import TestCase
from app.models import Event, FavoriteEvent, User
from django.utils import timezone
import datetime

class FavoriteEventTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="usuario123",
            email="usuario123@xd.com",
            password="usuario123",
        )
        self.event = Event.objects.create(
            title="Evento123",
            description="Buen Evento",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.user,
        )

    def test_add_event_to_favorites(self):
        """Test que verifica que un usuario puede agregar un evento a favoritos"""
        
        favorite = FavoriteEvent.objects.create(user=self.user, event=self.event)

        self.assertEqual(favorite.user, self.user)
        self.assertEqual(favorite.event, self.event)
        self.assertTrue(FavoriteEvent.objects.filter(user=self.user, event=self.event).exists())


    def test_remove_event_from_favorites(self):
        """Test que verifica que un usuario puede eliminar un evento de sus favoritos"""
        favorite = FavoriteEvent.objects.create(user=self.user, event=self.event)

        favorite.delete()

        self.assertFalse(FavoriteEvent.objects.filter(user=self.user, event=self.event).exists())



