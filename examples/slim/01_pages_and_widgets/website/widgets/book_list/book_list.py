from website_widgets import Widget

from website.models import Book


class BookList(Widget):
    """
    Every book, queried with the async ORM. The rows are fetched here, not left as a lazy queryset
    for the template: evaluating one there would run a synchronous query inside the page.
    """

    async def set_context(self):
        self.context.data['books'] = [book async for book in Book.objects.order_by('year')]
