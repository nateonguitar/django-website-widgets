from django.test import TestCase
from django.urls import reverse

from website.models import Book


class BookPageTestCase(TestCase):
    def test_book_page__shows_book__when_id_exists(self):
        book = Book.objects.get(title='Dune')

        response = self.client.get(reverse('website:BookPage', kwargs={'book_id': book.id}))

        self.assertContains(response, '<h1>Dune</h1>', html=False)
        self.assertContains(response, '<title>Dune | Pages and widgets</title>', html=False)

    def test_book_page__renders_not_found_variant_with_404__when_id_matches_nothing(self):
        response = self.client.get(reverse('website:BookPage', kwargs={'book_id': 999}))

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'No book 999', status_code=404)
        self.assertContains(response, 'book_page__not_found.html', status_code=404)
