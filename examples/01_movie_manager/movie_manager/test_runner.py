from unittest.mock import patch

from website_widgets.testing import WebsiteWidgetsTestRunner

from api.text_messages import TextMessages


class TestRunner(WebsiteWidgetsTestRunner):
    """The package's runner, which builds the frontend before browser tests, with no test ever texting anyone."""

    @classmethod
    def patches(cls) -> list:
        no_texts = patch.object(TextMessages, 'send')
        return [no_texts]
