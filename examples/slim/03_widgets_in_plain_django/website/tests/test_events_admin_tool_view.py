from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class EventsAdminToolViewTestCase(TestCase):
    def log_in_as_admin(self):
        self.client.force_login(User.objects.get(username='admin'))

    def test_events_tool__renders_table_inside_admin__when_staff(self):
        self.log_in_as_admin()

        response = self.client.get(reverse('admin:events_tool'))

        self.assertTemplateUsed(response, 'admin/base_site.html')
        self.assertContains(response, '<table id="example-events-table">')
        self.assertContains(response, 'Widget workshop')

    def test_events_tool__links_each_event_to_its_admin_change_page__when_staff(self):
        self.log_in_as_admin()

        response = self.client.get(reverse('admin:events_tool'))

        self.assertContains(response, '/admin/website/event/')

    def test_events_tool__redirects_to_admin_login__when_anonymous(self):
        response = self.client.get(reverse('admin:events_tool'))

        self.assertRedirects(response, f"{reverse('admin:login')}?next={reverse('admin:events_tool')}")

    def test_admin_index__links_events_tool__when_staff(self):
        self.log_in_as_admin()

        response = self.client.get(reverse('admin:index'))

        self.assertContains(response, f'href="{reverse("admin:events_tool")}"')
