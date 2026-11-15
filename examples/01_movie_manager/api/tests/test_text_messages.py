from unittest.mock import MagicMock

from django.test import SimpleTestCase

from api.text_messages import TextMessages


class TextMessagesTestCase(SimpleTestCase):
    def test_send__is_a_mock__in_every_test(self):
        # The test runner's patch, which under --parallel runs in a worker process that never
        # saw the main process's patches.
        self.assertIsInstance(TextMessages.send, MagicMock)
