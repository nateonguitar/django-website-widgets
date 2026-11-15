from bs4 import BeautifulSoup
from django.db.models import Prefetch
from django.utils import timezone

from api.models import Copy, Genre, Movie, MovieRating, Rental, User
from website.tests.app_widget_test_case import AppWidgetTestCase
from website.widgets.copy_table import CopyTable


class CopyTableTestCase(AppWidgetTestCase):
    """
    A SyncWidget three deep: the table, a row per copy, a Timestamp per date. Rendered with
    arender_document() all the same, since the document's appbar is an AsyncWidget; the table's
    set_context() makes no query, as the copies come in prefetched.
    """

    @classmethod
    def setUpTestData(cls):
        cls.alex = User.objects.get(username='alex')
        cls.jordan = User.objects.get(username='jordan')
        movie = Movie.objects.create(title='Up', year=2009, genre=Genre.ANIMATION, rating=MovieRating.PG)
        shelf, out, retired = Copy.objects.create_copies(movie, 3)
        Rental.objects.create(copy=out, user=cls.alex)
        retired.retired_at = timezone.now()
        retired.save()
        cls.movie = movie
        cls.shelf_label = shelf.label
        cls.out_label = out.label
        cls.retired_label = retired.label

    async def render_table(self, show_who: bool, viewer_id: int | None) -> dict[str, str]:
        """Where each copy is, by its label, as the table's last column says it."""
        # The prefetch MoviePage and the admin each make, which CopyTable's rows read.
        open_rentals = Rental.objects.filter(returned_at__isnull=True).select_related('user')
        copies = (
            Copy.objects
            .filter(movie=self.movie)
            .prefetch_related(Prefetch('rentals', queryset=open_rentals, to_attr='open_rentals'))
        )
        copies = [
            copy
            async for copy in copies
        ]
        copy_table = CopyTable(copies=copies, show_who=show_who, viewer_id=viewer_id)
        html = await self.arender_document(copy_table)
        soup = BeautifulSoup(html, 'html.parser')
        where = {}
        for row in soup.select('.copy-table tbody tr'):
            cells = row.select('td')
            label = cells[0].get_text(strip=True)
            words = cells[2].get_text().split()
            where[label] = ' '.join(words)
        return where

    async def test_copy_table__says_where_each_copy_is__when_viewer_has_one(self):
        where = await self.render_table(show_who=True, viewer_id=self.alex.id)

        shelf_copy = where[self.shelf_label]
        out_copy = where[self.out_label]
        retired_copy = where[self.retired_label]
        self.assertEqual(shelf_copy, 'On the shelf')
        self.assertEqual(out_copy, 'Out with you for less than a minute')
        self.assertEqual(retired_copy, 'Out of rotation')

    async def test_copy_table__names_who_has_it__when_someone_else_has_it(self):
        where = await self.render_table(show_who=True, viewer_id=self.jordan.id)

        out_copy = where[self.out_label]
        self.assertEqual(out_copy, 'Out with alex for less than a minute')

    async def test_copy_table__names_no_one__when_show_who_is_off(self):
        where = await self.render_table(show_who=False, viewer_id=None)

        out_copy = where[self.out_label]
        self.assertEqual(out_copy, 'Out')
