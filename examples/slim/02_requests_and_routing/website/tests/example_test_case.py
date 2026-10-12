from django.contrib.auth.models import User
from django.test import TestCase


class ExampleTestCase(TestCase):
    """Every test starts from the seeded users and articles, which the data migration creates."""

    def log_in_as(self, username: str):
        self.client.force_login(User.objects.get(username=username))
