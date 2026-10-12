from django.urls import reverse

from website.tests.example_test_case import ExampleTestCase


class ArticlePageTestCase(ExampleTestCase):
    def article_url(self, slug: str) -> str:
        return reverse('website:article', kwargs={'slug': slug})

    def test_article__renders__when_public(self):
        response = self.client.get(self.article_url('welcome'))

        self.assertContains(response, '<h1>Welcome</h1>', html=False)

    def test_article__renders_unauthorized_variant__when_members_only_and_logged_out(self):
        response = self.client.get(self.article_url('members-notes'))

        self.assertContains(response, 'site_page__unauthorized.html', status_code=401)
        self.assertContains(response, f'href="{reverse("login")}?next=', status_code=401)

    def test_article__renders__when_members_only_and_logged_in(self):
        self.log_in_as('reader')

        response = self.client.get(self.article_url('members-notes'))

        self.assertContains(response, "Members&#x27; notes")

    def test_article__renders_not_found_variant__when_slug_matches_nothing(self):
        response = self.client.get(self.article_url('no-such-article'))

        self.assertContains(response, 'site_page__not_found.html', status_code=404)

    def test_latest_article__redirects_to_newest__when_articles_exist(self):
        response = self.client.get(reverse('website:latest_article'))

        self.assertRedirects(response, self.article_url('loading-more'))
