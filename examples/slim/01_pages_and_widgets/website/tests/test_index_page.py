from django.test import TestCase
from django.urls import reverse

from website.models import Book


class IndexPageTestCase(TestCase):
    def test_index__links_every_demo__when_rendered(self):
        first_book = Book.objects.order_by('year').first()

        response = self.client.get(reverse('website:IndexPage'))

        self.assertContains(response, f'href="{reverse("website:CompositionPage")}"')
        self.assertContains(response, f'href="{reverse("website:AsyncPage")}"')
        self.assertContains(response, f'href="{reverse("website:BookPage", kwargs={"book_id": first_book.id})}"')

    def test_index__links_static_stylesheet_and_script__when_rendered(self):
        response = self.client.get(reverse('website:IndexPage'))

        self.assertContains(response, '<link rel="stylesheet" href="/static/website/styles.css">')
        self.assertContains(response, '<script src="/static/website/analytics.js" defer></script>')
