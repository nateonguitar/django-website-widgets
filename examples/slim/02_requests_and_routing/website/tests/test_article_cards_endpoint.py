from django.urls import reverse

from website.tests.example_test_case import ExampleTestCase


class ArticleCardsEndpointTestCase(ExampleTestCase):
    def test_article_cards__returns_next_cards__when_offset_given(self):
        response = self.client.get(reverse('api_article_cards'), {'offset': 3})

        data = response.json()
        self.assertEqual(data['html'].count('example-article-card'), 2)
        self.assertEqual(data['next_offset'], 5)
        self.assertFalse(data['has_more'])

    def test_article_cards__returns_the_markup_the_page_renders__when_same_article(self):
        endpoint_html = self.client.get(reverse('api_article_cards'), {'offset': 0}).json()['html']
        page_html = self.client.get(reverse('website:articles')).content.decode()

        self.assertIn(endpoint_html.split('</a>')[0], page_html)
