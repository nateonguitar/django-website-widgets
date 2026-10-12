from django.core.exceptions import SynchronousOnlyOperation

from website_widgets import Widget

from website.models import Book


class SyncOrmTrapNote(Widget):
    """
    Runs a synchronous query in a plain `def set_context()` on purpose, and shows the error Django
    raises, which would otherwise fail the page. It catches it only so the demo page still renders.
    """

    def set_context(self):
        try:
            self.context.data['book_count'] = Book.objects.count()
            self.context.data['error'] = None
        except SynchronousOnlyOperation as error:
            self.context.data['error'] = f'{type(error).__name__}: {error}'
