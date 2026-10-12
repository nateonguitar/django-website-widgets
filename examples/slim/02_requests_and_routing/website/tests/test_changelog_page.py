from django.urls import reverse

from website.models import Article
from website.tests.example_test_case import ExampleTestCase


class ChangelogPageTestCase(ExampleTestCase):
    def test_changelog__returns_not_modified__when_etag_matches(self):
        etag = self.client.get(reverse('website:changelog'))['ETag']

        response = self.client.get(reverse('website:changelog'), HTTP_IF_NONE_MATCH=etag)

        self.assertEqual(response.status_code, 304)
        self.assertEqual(response.content, b'')

    def test_changelog__changes_etag__when_an_article_is_added(self):
        etag = self.client.get(reverse('website:changelog'))['ETag']
        newest = Article.objects.first()
        Article.objects.create(
            slug='another',
            title='Another',
            summary='One more.',
            body='One more.',
            published_at=newest.published_at)

        response = self.client.get(reverse('website:changelog'), HTTP_IF_NONE_MATCH=etag)

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response['ETag'], etag)

    def test_changelog__changes_etag__when_viewer_changes(self):
        logged_out_etag = self.client.get(reverse('website:changelog'))['ETag']
        self.log_in_as('reader')

        logged_in_etag = self.client.get(reverse('website:changelog'))['ETag']

        self.assertNotEqual(logged_in_etag, logged_out_etag)
