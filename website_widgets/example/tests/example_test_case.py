import json

from django.test import TestCase, override_settings

from website_widgets.example.projects.store import Store
from website_widgets.example.projects.viewer_cookie import ViewerCookie


@override_settings(ROOT_URLCONF='website_widgets.example.urls')
class ExampleTestCase(TestCase):
    """
    Mounts the example URLs at the root, so `reverse()` works whether or not the host project
    installs the example app, and starts each test from the seed data.
    """

    USER_1 = 1
    USER_2 = 2
    ADMIN = 3

    def setUp(self):
        super().setUp()
        Store.reset()

    def log_in_as(self, user_id: int):
        self.client.cookies[ViewerCookie.NAME] = str(user_id)

    def send_json(self, method: str, url: str, data=None):
        return getattr(self.client, method)(
            url,
            data=json.dumps(data) if data is not None else None,
            content_type='application/json')
