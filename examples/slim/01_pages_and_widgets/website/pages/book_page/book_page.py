from website_widgets import register_url

from website.models import Book
from website.pages.example_page import ExamplePage


@register_url('books/<int:book_id>/')
class BookPage(ExamplePage):
    """
    One book, or, when the id matches nothing, `book_page__not_found.html` with a 404. The variant
    is picked in `set_context()`, which runs before any template is chosen.
    """

    def __init__(self, book_id: int):
        super().__init__()
        self.book_id = book_id

    async def set_context(self):
        book = await Book.objects.filter(pk=self.book_id).afirst()
        if book is None:
            self.status_code = 404
            self.template_filename = 'book_page__not_found.html'
            self.page_title = 'Book not found'
            super().set_context()
            self.context.data['book_id'] = self.book_id
            return
        self.page_title = book.title
        self.page_description = f'{book.title} by {book.author}.'
        super().set_context()
        self.context.data['book'] = book
        self.context.data['next_book'] = await Book.objects.filter(year__gt=book.year).order_by('year').afirst()
