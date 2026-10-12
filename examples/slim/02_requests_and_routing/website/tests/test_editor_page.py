from django.urls import reverse

from website.tests.example_test_case import ExampleTestCase


class EditorPageTestCase(ExampleTestCase):
    def test_editor__renders_unauthorized_variant__when_logged_out(self):
        response = self.client.get(reverse('website:editor'))

        self.assertContains(response, 'site_page__unauthorized.html', status_code=401)

    def test_editor__renders_forbidden_variant__when_not_staff(self):
        self.log_in_as('reader')

        response = self.client.get(reverse('website:editor'))

        self.assertContains(response, 'site_page__forbidden.html', status_code=403)

    def test_editor__lists_every_article__when_staff(self):
        self.log_in_as('editor')

        response = self.client.get(reverse('website:editor'))

        self.assertContains(response, 'members-notes')
        self.assertContains(response, 'loading-more')
