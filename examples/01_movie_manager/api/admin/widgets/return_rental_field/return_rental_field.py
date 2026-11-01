from django.urls import reverse
from website_widgets import SyncWidget

from api.models import Rental
from website.widgets.timestamp import Timestamp, TimestampStyle


class ReturnRentalField(SyncWidget):
    """
    The Rental admin's "Returned" field: when the copy came back, or, while it's still out, a
    Return button that calls the same return endpoint the site's My movies page does. Only the
    admin uses it, so its behavior is a few lines of vanilla JavaScript in its own template, not
    a controller in the site's bundle: it works wherever the admin does, with no build.
    """

    def __init__(self, rental: Rental):
        """`rental` with its `user` loaded, since the template names who has it."""
        super().__init__()
        self.rental = rental

    def set_context(self):
        self.context.data['rental'] = self.rental
        # The site's own Timestamp, nested inside this admin-only widget, so a date reads the
        # same in the admin as on every page.
        if self.rental.returned_at is None:
            self.context.data['return_url'] = reverse('api:return_rental', args=[self.rental.id])
            self.context.children['out_for'] = Timestamp(value=self.rental.taken_at, style=TimestampStyle.DURATION)
        else:
            self.context.children['returned'] = Timestamp(value=self.rental.returned_at, style=TimestampStyle.AGO)
