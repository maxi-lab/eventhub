import datetime
from django.test import TestCase
from django.utils import timezone
from app.models import Event, User,Category,Venue

class EventModelTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )
        self.state="CANCELADO"
       # Crear categoría y venue necesarios para los eventos
        self.category = Category.objects.create(
            name="Test Category",
            description="Test Description"
        )
        self.venue = Venue.objects.create(
            name="Test Venue",
            address="Test Address",
            city="Test City",
            capacity=100,
            contact="Test Contact"
        )

    def test_event_creation(self):
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            category=self.category,
            venue=self.venue
        )
        """Test que verifica la creación correcta de eventos"""
        self.assertEqual(event.title, "Evento de prueba")
        self.assertEqual(event.description, "Descripción del evento de prueba")
        self.assertEqual(event.organizer, self.organizer)
        self.assertIsNotNone(event.created_at)
        self.assertIsNotNone(event.updated_at)

    def test_event_validate_with_valid_data(self):
        """Test que verifica la validación de eventos con datos válidos"""
        scheduled_at = timezone.now() + datetime.timedelta(days=1)
        errors = Event.validate("Título válido", "Descripción válida", scheduled_at)
        self.assertEqual(errors, {})

    def test_event_validate_with_empty_title(self):
        """Test que verifica la validación de eventos con título vacío"""
        scheduled_at = timezone.now() + datetime.timedelta(days=1)
        errors = Event.validate("", "Descripción válida", scheduled_at)
        self.assertIn("title", errors)
        self.assertEqual(errors["title"], "Por favor ingrese un titulo")

    def test_event_validate_with_empty_description(self):
        """Test que verifica la validación de eventos con descripción vacía"""
        scheduled_at = timezone.now() + datetime.timedelta(days=1)
        errors = Event.validate("Título válido", "", scheduled_at)
        self.assertIn("description", errors)
        self.assertEqual(errors["description"], "Por favor ingrese una descripcion")

    def test_event_new_with_valid_data(self):
        """Test que verifica la creación de eventos con datos válidos"""
        scheduled_at = timezone.now() + datetime.timedelta(days=2)
        success, errors = Event.new(
            title="Nuevo evento",
            description="Descripción del nuevo evento",
            scheduled_at=scheduled_at,
            organizer=self.organizer,
            venue=None,
            category=None
        )

        self.assertTrue(success)
        self.assertIsNone(errors)

        # Verificar que el evento fue creado en la base de datos
        new_event = Event.objects.get(title="Nuevo evento")
        self.assertEqual(new_event.description, "Descripción del nuevo evento")
        self.assertEqual(new_event.organizer, self.organizer)

    def test_event_new_with_invalid_data(self):
        """Test que verifica que no se crean eventos con datos inválidos"""
        scheduled_at = timezone.now() + datetime.timedelta(days=2)
        initial_count = Event.objects.count()

        # Intentar crear evento con título vacío
        success, errors = Event.new(
            title="",
            description="Descripción del evento",
            scheduled_at=scheduled_at,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category
        )

        self.assertFalse(success)
        self.assertIn("title", errors)

        # Verificar que no se creó ningún evento nuevo
        self.assertEqual(Event.objects.count(), initial_count)

    def test_event_update(self):
        """Test que verifica la actualización de eventos"""
        new_title = "Título actualizado"
        new_description = "Descripción actualizada"
        new_scheduled_at = timezone.now() + datetime.timedelta(days=3)

        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            category=self.category

        )

        event.update(
            title=new_title,
            description=new_description,
            scheduled_at=new_scheduled_at,
            organizer=self.organizer,
            category=self.category,
            venue=self.venue,
            state=self.state

        )

        # Recargar el evento desde la base de datos
        updated_event = Event.objects.get(pk=event.pk)

        self.assertEqual(updated_event.title, new_title)
        self.assertEqual(updated_event.description, new_description)
        self.assertEqual(updated_event.scheduled_at.time(), new_scheduled_at.time())

    def test_event_update_partial(self):
        """Test que verifica la actualización parcial de eventos"""
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            category=self.category,
            venue=self.venue
        )

        original_title = event.title
        original_scheduled_at = event.scheduled_at
        new_description = "Solo la descripción ha cambiado"

        event.update(
            title=None,  # No cambiar
            description=new_description,
            scheduled_at=None,  # No cambiar
            organizer=None,  # No cambiar
            category=None, 
            venue=None,
            state=None

        )

        # Recargar el evento desde la base de datos
        updated_event = Event.objects.get(pk=event.pk)

        # Verificar que solo cambió la descripción
        self.assertEqual(updated_event.title, original_title)
        self.assertEqual(updated_event.description, new_description)
        self.assertEqual(updated_event.scheduled_at, original_scheduled_at)

    def test_event_update_state(self):
        """Testea que se actualize el estado"""
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
        )
        original_title = event.title
        original_description=event.description
        new_state=self.state
        original_scheduled_at = event.scheduled_at
        event.update(
            title=None,  
            description=None,
            scheduled_at=None, 
            organizer=None,  
            category=None, 
            venue=None,
            state=self.state
        )
        updated_event = Event.objects.get(pk=event.pk)
        self.assertEqual(updated_event.title, original_title)
        self.assertEqual(updated_event.description,original_description)
        self.assertEqual(updated_event.state, new_state)
        self.assertEqual(updated_event.scheduled_at, original_scheduled_at)
        


class EventFilterTest(TestCase):
    def setUp(self):
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="test_organizer",
            email="organizer@test.com",
            password="testpass123",
            is_organizer=True
        )
        
        # Crear categoría y venue necesarios
        self.category = Category.objects.create(
            name="Test Category",
            description="Test Description"
        )
        self.venue = Venue.objects.create(
            name="Test Venue",
            address="Test Address",
            city="Test City",
            capacity=100,
            contact="Test Contact"
        )

        # Crear eventos de prueba
        self.now = timezone.now()
        
        # Evento pasado (ayer)
        self.past_event = Event.objects.create(
            title="Evento Pasado",
            description="Descripción del evento pasado",
            scheduled_at=self.now - datetime.timedelta(days=1),
            organizer=self.organizer,
            category=self.category,
            venue=self.venue
        )

        # Evento futuro (mañana)
        self.future_event = Event.objects.create(
            title="Evento Futuro",
            description="Descripción del evento futuro",
            scheduled_at=self.now + datetime.timedelta(days=1),
            organizer=self.organizer,
            category=self.category,
            venue=self.venue
        )

    def test_filter_past_events(self):
        """Test que verifica el filtrado de eventos pasados"""
        past_events = Event.objects.filter(scheduled_at__lt=self.now)
        self.assertEqual(past_events.count(), 1)
        self.assertEqual(past_events[0], self.past_event)

    def test_filter_current_and_future_events(self):
        """Test que verifica el filtrado de eventos actuales y futuros"""
        future_events = Event.objects.filter(scheduled_at__gte=self.now)
        self.assertEqual(future_events.count(), 1)
        self.assertEqual(future_events[0], self.future_event)

