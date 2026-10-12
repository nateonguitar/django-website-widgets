from django.urls import reverse

from website_widgets import register_url

from website.models import Book
from website.pages.example_page import ExamplePage


@register_url('')
class IndexPage(ExamplePage):
    # Async, because it queries: a page renders inside an async view, where the sync ORM raises.
    async def set_context(self):
        super().set_context()
        first_book = await Book.objects.order_by('year').afirst()
        self.context.data['demos'] = [
            {
                'name': 'Composition',
                'url': reverse('website:CompositionPage'),
                'description': (
                    'A page as a tree of widgets: data passed down through constructors, a list of '
                    'children, a skipped child and the shared page context.'),
            },
            {
                'name': 'Async widgets',
                'url': reverse('website:AsyncPage'),
                'description': (
                    'Awaiting in set_context(): the async ORM, slow calls one after another or '
                    'gathered by a parent, and what a synchronous query does inside a page.'),
            },
            {
                'name': 'Variant templates',
                'url': reverse('website:BookPage', kwargs={'book_id': first_book.id if first_book else 1}),
                'description': (
                    'One page, two renders: a book, or book_page__not_found.html with a 404 when the '
                    'id matches nothing.'),
            },
        ]
