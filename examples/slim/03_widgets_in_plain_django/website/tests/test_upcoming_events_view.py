from django.test import TestCase
from django.urls import reverse

from website.models import Event


class UpcomingEventsViewTestCase(TestCase):
    def test_upcoming_events__renders_widget_html_inside_base_template__when_rendered(self):
        response = self.client.get(reverse('upcoming_events'))

        self.assertTemplateUsed(response, 'website/base.html')
        self.assertContains(response, 'class="example-card example-event-card"', count=Event.objects.count())

    def test_upcoming_events__outputs_widget_html_unescaped__when_rendered(self):
        response = self.client.get(reverse('upcoming_events'))

        self.assertContains(response, '<h3>Widget workshop</h3>', html=False)
        self.assertNotContains(response, '&lt;article')

    def test_upcoming_events__keeps_each_cards_inline_script__when_card_has_a_description(self):
        response = self.client.get(reverse('upcoming_events'))

        described_count = Event.objects.exclude(description='').count()
        self.assertContains(response, 'class="example-button example-button-secondary example-event-toggle"', count=described_count)

    def test_upcoming_events__links_static_stylesheet_and_script__when_rendered(self):
        response = self.client.get(reverse('upcoming_events'))

        self.assertContains(response, 'href="/static/website/styles.css"')
        self.assertContains(response, 'src="/static/website/analytics.js"')
