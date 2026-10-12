from django.core.mail import EmailMultiAlternatives
from django.urls import reverse

from website_widgets import Widget

from website.models import Event
from website.widgets.email_document.email_document import EmailDocument


class Email:
    """
    The base of every email: its HTML is an `EmailDocument` widget around the email's own
    content widget, rendered with `render()` and no request, beside a plain-text version.

    Sent from management commands, so links are absolute, built from `site_url`, since an email
    has no host to be relative to.
    """

    def __init__(self, site_url: str):
        self.site_url = site_url.rstrip('/')

    def get_subject(self) -> str:
        raise NotImplementedError('Each email sets its own subject.')

    def get_text_body(self) -> str:
        """The plain-text version, for mail apps that don't show HTML."""
        raise NotImplementedError('Each email writes its own plain-text body.')

    def build_content(self) -> Widget:
        """The widget for this email's own part, between the shared header and footer."""
        raise NotImplementedError('Each email builds its own content widget.')

    def get_events_url(self) -> str:
        return f"{self.site_url}{reverse('upcoming_events')}"

    def get_event_url(self, event: Event) -> str:
        """The event's card on the events page, which has the card's id."""
        return f'{self.get_events_url()}#example-event-{event.id}'

    def render_html(self) -> str:
        document = EmailDocument(
            subject=self.get_subject(),
            events_url=self.get_events_url(),
            content=self.build_content())
        return document.render()

    def send(self, to: str):
        message = EmailMultiAlternatives(
            subject=self.get_subject(),
            body=self.get_text_body(),
            to=[to])
        message.attach_alternative(self.render_html(), 'text/html')
        message.send()
