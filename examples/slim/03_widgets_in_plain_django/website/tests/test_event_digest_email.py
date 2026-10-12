from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from website.emails.event_digest_email import EventDigestEmail
from website.models import Event


class EventDigestEmailTestCase(TestCase):
    def html_body(self) -> str:
        html_body, _mimetype = mail.outbox[0].alternatives[0]
        return html_body

    def test_send__wraps_digest_in_email_document__when_sent(self):
        EventDigestEmail(events=list(Event.objects.all()), site_url='https://example.com').send(to='someone@example.com')

        self.assertTrue(self.html_body().startswith('<!DOCTYPE html>'))
        self.assertIn('<title>Upcoming events</title>', self.html_body())
        self.assertIn('See every upcoming event', self.html_body())

    def test_send__links_each_event_absolutely__when_sent_without_a_request(self):
        event = Event.objects.get(name='Widget workshop')

        EventDigestEmail(events=[event], site_url='https://example.com/').send(to='someone@example.com')

        self.assertEqual(mail.outbox[0].to, ['someone@example.com'])
        self.assertIn(f'href="https://example.com/#example-event-{event.id}"', self.html_body())
        self.assertIn(f'https://example.com/#example-event-{event.id}', mail.outbox[0].body)

    def test_send_event_digest__sends_one_email__when_run(self):
        call_command('send_event_digest', to='someone@example.com')

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(f'{Event.objects.count()} events coming up', self.html_body())
