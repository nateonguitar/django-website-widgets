import json

from django.contrib.auth.models import User
from django.test import TestCase

from website.models import Project


class TrackerTestCase(TestCase):
    """Every test starts from the seeded users and projects, which the data migration creates."""

    USER_1 = 'user_1'
    USER_2 = 'user_2'
    ADMIN = 'admin'

    def log_in_as(self, username: str):
        self.client.force_login(User.objects.get(username=username))

    def project_named(self, name: str) -> Project:
        return Project.objects.get(name=name)

    def send_json(self, method: str, url: str, data=None):
        return getattr(self.client, method)(
            url,
            data=json.dumps(data) if data is not None else None,
            content_type='application/json')
