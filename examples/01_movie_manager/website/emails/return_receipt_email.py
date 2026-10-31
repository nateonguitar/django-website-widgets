from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse

from api.models import Rental, User
from website.widgets.emails.email_document import EmailDocument
from website.widgets.emails.return_receipt import ReturnReceipt


class ReturnReceiptEmail:
    """
    Sent when someone brings a movie back. Built like CheckoutReceiptEmail: its own content
    widget inside the EmailDocument, so it ends in the same EmailFooter.
    """

    def __init__(self, user: User, rental: Rental):
        """`rental` with `copy.movie` loaded."""
        self.user = user
        self.rental = rental

    def subject(self) -> str:
        return f'{self.rental.copy.movie.title} is back on the shelf'

    def text_body(self) -> str:
        home_url = f'{settings.SITE_URL}{reverse("website:HomePage")}'
        lines = [
            f'Thanks for bringing it back, {self.user.username}.',
            '',
            f'{self.rental.copy.movie.title} ({self.rental.copy.movie.year}) is back on the shelf.',
            '',
            f"Looking for the next one? See what's new: {home_url}",
        ]
        return '\n'.join(lines)

    def html_body(self) -> str:
        content = ReturnReceipt(username=self.user.username, rental=self.rental)
        document = EmailDocument(subject=self.subject(), site_url=settings.SITE_URL, content=content)
        return document.render()

    def send(self) -> None:
        message = EmailMultiAlternatives(
            subject=self.subject(),
            body=self.text_body(),
            to=[self.user.email])
        message.attach_alternative(self.html_body(), 'text/html')
        message.send()
