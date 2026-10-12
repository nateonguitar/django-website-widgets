from django.contrib.auth.hashers import make_password
from django.db import migrations


# Every seeded user's, for a local demo. Not "password": browsers warn about a password found in
# data breaches, on every login.
PASSWORD = 'try-the-widgets'
# (username, first name, last name, is_staff)
USERS = [
    ('user_1', 'Riley', 'Park', False),
    ('user_2', 'Jordan', 'Avery', False),
    ('admin', 'Site', 'Admin', True),
]
# (owner's username, name, description)
PROJECTS = [
    ('user_1', 'Garden planner', 'Which vegetables go in which bed, and when to plant them.'),
    ('user_2', 'Reading list', 'Books to read this year, with a line on each one once finished.'),
]


class SeedUsersAndProjects:
    """The users and projects every page and test starts from, so `migrate` gives a working site."""

    @staticmethod
    def add(apps, schema_editor):
        user_model = apps.get_model('auth', 'User')
        users = {
            username: user_model.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff,
                password=make_password(PASSWORD))
            for username, first_name, last_name, is_staff in USERS
        }
        project_model = apps.get_model('website', 'Project')
        project_model.objects.bulk_create([
            project_model(name=name, description=description, created_by=users[owner])
            for owner, name, description in PROJECTS
        ])

    @staticmethod
    def remove(apps, schema_editor):
        apps.get_model('auth', 'User').objects.filter(username__in=[user[0] for user in USERS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('website', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(SeedUsersAndProjects.add, SeedUsersAndProjects.remove),
    ]
