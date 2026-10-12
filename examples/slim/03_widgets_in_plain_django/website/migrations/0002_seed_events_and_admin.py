from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.db import migrations
from django.utils import timezone


# The admin's, for a local demo. Not "password": browsers warn about a password found in data
# breaches, on every login.
PASSWORD = 'try-the-widgets'
# (name, days from when `migrate` runs, location, description). Relative, so they stay upcoming.
EVENTS = [
    ('Widget workshop', 3, 'Room 1', 'Build a page from widgets, start to finish.'),
    ('Async ORM office hours', 10, 'Online', 'Bring the query that raised SynchronousOnlyOperation.'),
    ('Template lookup deep dive', 17, 'Room 2', ''),
    ('Release party', 30, 'The roof', 'Celebrating the next django-website-widgets release.'),
]


class SeedEventsAndAdmin:
    """
    The events every view and test starts from, and an `admin` superuser to open the admin tool
    page with.
    """

    @staticmethod
    def add(apps, schema_editor):
        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        event_model = apps.get_model('website', 'Event')
        event_model.objects.bulk_create([
            event_model(
                name=name,
                starts_at=now + timedelta(days=days),
                location=location,
                description=description)
            for name, days, location, description in EVENTS
        ])
        apps.get_model('auth', 'User').objects.create(
            username='admin',
            is_staff=True,
            is_superuser=True,
            password=make_password(PASSWORD))

    @staticmethod
    def remove(apps, schema_editor):
        apps.get_model('website', 'Event').objects.filter(name__in=[event[0] for event in EVENTS]).delete()
        apps.get_model('auth', 'User').objects.filter(username='admin').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('website', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(SeedEventsAndAdmin.add, SeedEventsAndAdmin.remove),
    ]
