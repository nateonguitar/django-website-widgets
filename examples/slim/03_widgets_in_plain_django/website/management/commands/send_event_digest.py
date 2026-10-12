from django.core.management.base import BaseCommand
from django.utils import timezone

from website.emails.event_digest_email import EventDigestEmail
from website.models import Event


class Command(BaseCommand):
    help = 'Emails a digest of the upcoming events. The example prints emails to the console.'

    def add_arguments(self, parser):
        parser.add_argument('--to', required=True, help='The address to send the digest to.')
        parser.add_argument(
            '--site-url',
            default='http://localhost:8000',
            help="Prefixed to each link, since an email has no host to be relative to.")

    def handle(self, *args, **options):
        events = list(Event.objects.filter(starts_at__gte=timezone.now()))
        email = EventDigestEmail(events=events, site_url=options['site_url'])
        email.send(to=options['to'])
