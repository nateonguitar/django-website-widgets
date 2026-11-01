from django.test import SimpleTestCase

from website_widgets.widget import AsyncWidget, SyncWidget, _Widget


class WidgetClassesTestCase(SimpleTestCase):
    def test_async_widget__fails_at_definition__when_set_context_is_def(self):
        with self.assertRaisesMessage(TypeError, 'LikeButton.set_context() is `def`, but LikeButton is an AsyncWidget: write `async def set_context()`, or subclass SyncWidget.'):
            class LikeButton(AsyncWidget):
                def set_context(self):
                    pass

    def test_sync_widget__fails_at_definition__when_set_context_is_async(self):
        with self.assertRaisesMessage(TypeError, 'EmailBody.set_context() is `async def`, but EmailBody is a SyncWidget: write `def set_context()`, or subclass AsyncWidget.'):
            class EmailBody(SyncWidget):
                async def set_context(self):
                    pass

    def test_widget__fails_at_definition__when_private_base_subclassed(self):
        with self.assertRaisesMessage(TypeError, 'subclass AsyncWidget or SyncWidget instead'):
            class LikeButton(_Widget):
                pass

    def test_widget_classes__define__when_set_context_left_to_base_or_inherited(self):
        class AsyncCard(AsyncWidget):
            pass

        class SyncCard(SyncWidget):
            pass

        class FeaturedCard(AsyncCard):
            pass

        self.assertTrue(issubclass(FeaturedCard, AsyncWidget))
        self.assertTrue(issubclass(SyncCard, SyncWidget))
