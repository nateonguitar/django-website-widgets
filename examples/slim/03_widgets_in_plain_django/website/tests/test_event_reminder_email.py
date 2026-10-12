from django.core import mail
from django.core.management import CommandError, call_command
from django.test import TestCase

from website.emails.event_reminder_email import EventReminderEmail
from website.models import Event


class EventReminderEmailTestCase(TestCase):
    def html_body(self) -> str:
        html_body, _mimetype = mail.outbox[0].alternatives[0]
        return html_body

    def test_send__wraps_event_in_email_document__when_sent(self):
        event = Event.objects.get(name='Widget workshop')

        EventReminderEmail(event=event, site_url='https://example.com').send(to='someone@example.com')

        self.assertEqual(mail.outbox[0].subject, 'Coming up: Widget workshop')
        self.assertTrue(self.html_body().startswith('<!DOCTYPE html>'))
        self.assertIn('See every upcoming event', self.html_body())
        self.assertIn('Build a page from widgets, start to finish.', self.html_body())
        self.assertIn(f'https://example.com/#example-event-{event.id}', mail.outbox[0].body)

    def test_send_event_reminder__reminds_of_next_event__when_run(self):
        call_command('send_event_reminder', to='someone@example.com')

        self.assertEqual(mail.outbox[0].subject, f'Coming up: {Event.objects.first().name}')

    def test_send_event_reminder__fails__when_no_event_upcoming(self):
        Event.objects.all().delete()

        with self.assertRaises(CommandError):
            call_command('send_event_reminder', to='someone@example.com')
