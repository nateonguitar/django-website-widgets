from django.test import SimpleTestCase

from website_widgets.example.advanced.widgets.tip_card.tip_card import TipCard


class TipCardTestCase(SimpleTestCase):
    """Renders the widget on its own, with no page and no test client."""

    def test_tip_card__shows_number_and_tip__when_rendered(self):
        html = TipCard(number=0).render__test_sync()

        self.assertIn('Tip 0', html)
        self.assertIn('through its constructor', html)

    def test_tip_card__wraps_around__when_number_past_last_tip(self):
        html = TipCard(number=len(TipCard.TIPS) + 1).render__test_sync()

        self.assertIn('context.page, shared by reference', html)
