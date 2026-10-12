from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from website.emails.event_reminder_email import EventReminderEmail
from website.models import Event


class Command(BaseCommand):
    help = 'Emails a reminder of the next upcoming event. The example prints emails to the console.'

    def add_arguments(self, parser):
        parser.add_argument('--to', required=True, help='The address to send the reminder to.')
        parser.add_argument(
            '--site-url',
            default='http://localhost:8000',
            help="Prefixed to each link, since an email has no host to be relative to.")

    def handle(self, *args, **options):
        event = Event.objects.filter(starts_at__gte=timezone.now()).first()
        if event is None:
            raise CommandError('No upcoming event to remind anyone of.')
        email = EventReminderEmail(event=event, site_url=options['site_url'])
        email.send(to=options['to'])
