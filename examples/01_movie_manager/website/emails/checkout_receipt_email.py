from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse

from api.models import Rental, User
from website.widgets.emails.checkout_receipt import CheckoutReceipt
from website.widgets.emails.email_document import EmailDocument


class CheckoutReceiptEmail:
    """
    Sent when someone takes movies home. Its three parts sit together: the subject, a plain-text
    body for mail apps that don't show HTML, and the HTML, built from widgets with render().
    Sync throughout, as email sending is, so it's sent from the checkout endpoint through
    sync_to_async.
    """

    def __init__(self, user: User, rentals: list[Rental]):
        """`rentals` each with `copy.movie` loaded."""
        self.user = user
        self.rentals = rentals

    def subject(self) -> str:
        count = len(self.rentals)
        return f'You took home {count} movie{"" if count == 1 else "s"}'

    def text_body(self) -> str:
        # Written out, not stripped from the HTML, so the link reads as a full URL.
        my_movies_url = f'{settings.SITE_URL}{reverse("website:MyMoviesPage")}'
        titles = [f'- {rental.copy.movie.title} ({rental.copy.movie.year})' for rental in self.rentals]
        lines = [
            f'Enjoy the movies, {self.user.username}.',
            '',
            'You took home:',
            *titles,
            '',
            f"When they're back on the shelf, return them from My movies: {my_movies_url}",
        ]
        return '\n'.join(lines)

    def html_body(self) -> str:
        content = CheckoutReceipt(username=self.user.username, rentals=self.rentals)
        document = EmailDocument(subject=self.subject(), site_url=settings.SITE_URL, content=content)
        return document.render()

    def send(self) -> None:
        message = EmailMultiAlternatives(
            subject=self.subject(),
            body=self.text_body(),
            to=[self.user.email])
        message.attach_alternative(self.html_body(), 'text/html')
        message.send()
