import io

from django.core.management import call_command
from django.urls import resolve, reverse

from website.pages.about_page.about_page import AboutPage
from website.pages.article_page.article_page import ArticlePage
from website.pages.latest_article_page.latest_article_page import LatestArticlePage
from website.tests.example_test_case import ExampleTestCase


class RoutingTestCase(ExampleTestCase):
    def test_about__is_reached_by_hand__when_listed_in_urls_py(self):
        match = resolve(reverse('about'))

        self.assertIs(match.func.view_class, AboutPage)
        self.assertEqual(match.namespace, '')

    def test_article__is_reached_through_discovery__when_decorated(self):
        match = resolve(reverse('website:article', kwargs={'slug': 'welcome'}))

        self.assertIs(match.func.view_class, ArticlePage)
        self.assertEqual(match.namespace, 'website')

    def test_latest__wins_over_slug_route__when_both_match(self):
        match = resolve('/articles/latest/')

        self.assertIs(match.func.view_class, LatestArticlePage)

    def test_show_routes__succeeds__when_every_route_reaches_its_page(self):
        output = io.StringIO()

        call_command('ww_show_routes', stdout=output, no_color=True)

        self.assertIn('All 6 page routes reach their page.', output.getvalue())
        self.assertLess(output.getvalue().index('/articles/latest/'), output.getvalue().index('/articles/<slug:slug>/'))
