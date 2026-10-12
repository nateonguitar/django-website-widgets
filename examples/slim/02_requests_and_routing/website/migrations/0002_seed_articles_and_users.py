from datetime import datetime, timezone

from django.contrib.auth.hashers import make_password
from django.db import migrations


# Every seeded user's, for a local demo. Not "password": browsers warn about a password found in
# data breaches, on every login.
PASSWORD = 'try-the-widgets'
# (username, is_staff)
USERS = [
    ('reader', False),
    ('editor', True),
]
# (slug, title, summary, body, members_only, published)
ARTICLES = [
    (
        'welcome',
        'Welcome',
        'What this example covers.',
        'Each page here shows one way a request reaches a page, or one way a page can answer it.',
        False,
        datetime(2026, 1, 5, tzinfo=timezone.utc),
    ),
    (
        'routing-pages',
        'Routing pages',
        'Hand-routed pages beside @register_url.',
        'Most pages declare their own route. The About page is routed in urls.py instead, and the two mix freely.',
        False,
        datetime(2026, 2, 9, tzinfo=timezone.utc),
    ),
    (
        'answering-a-request',
        'Answering a request',
        'Variants, redirects and 304s from handle_request().',
        'A page can answer with a different template, send the browser somewhere else, or say nothing changed.',
        False,
        datetime(2026, 3, 16, tzinfo=timezone.utc),
    ),
    (
        'members-notes',
        "Members' notes",
        'Open to logged-in readers only.',
        "You're reading this because you're logged in. Any account will do; it doesn't need to be staff.",
        True,
        datetime(2026, 4, 20, tzinfo=timezone.utc),
    ),
    (
        'loading-more',
        'Loading more',
        'Server-rendered cards from an endpoint with arender().',
        'The articles list renders its first cards with the page. The rest come from an endpoint that renders the same widget.',
        False,
        datetime(2026, 5, 25, tzinfo=timezone.utc),
    ),
]


class SeedArticlesAndUsers:
    """The users and articles every page and test starts from, so `migrate` gives a working site."""

    @staticmethod
    def add(apps, schema_editor):
        user_model = apps.get_model('auth', 'User')
        for username, is_staff in USERS:
            user_model.objects.create(
                username=username,
                is_staff=is_staff,
                password=make_password(PASSWORD))
        article_model = apps.get_model('website', 'Article')
        article_model.objects.bulk_create([
            article_model(
                slug=slug,
                title=title,
                summary=summary,
                body=body,
                members_only=members_only,
                published_at=published_at)
            for slug, title, summary, body, members_only, published_at in ARTICLES
        ])

    @staticmethod
    def remove(apps, schema_editor):
        apps.get_model('website', 'Article').objects.filter(slug__in=[article[0] for article in ARTICLES]).delete()
        apps.get_model('auth', 'User').objects.filter(username__in=[user[0] for user in USERS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('website', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(SeedArticlesAndUsers.add, SeedArticlesAndUsers.remove),
    ]
