import random

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class User(AbstractUser):
    """
    Django's user, as the project's own class from the first migration, so a field can be added
    later without the migration Django can't do once `auth.User` has rows.
    """


class Genre(models.TextChoices):
    ACTION = 'action', 'Action'
    ANIMATION = 'animation', 'Animation'
    COMEDY = 'comedy', 'Comedy'
    DRAMA = 'drama', 'Drama'
    FAMILY = 'family', 'Family'
    HORROR = 'horror', 'Horror'
    SCIENCE_FICTION = 'science_fiction', 'Science fiction'


class MovieRating(models.TextChoices):
    G = 'G', 'G'
    PG = 'PG', 'PG'
    PG13 = 'PG13', 'PG-13'
    R = 'R', 'R'
    NC17 = 'NC17', 'NC-17'

    @property
    def description(self) -> str:
        """What the rating roughly means, which RatingPicker shows beside the choice."""
        descriptions = {
            'G': 'General audiences: fine for all ages.',
            'PG': 'Parental guidance suggested: some material may not suit young children.',
            'PG13': 'Parents strongly cautioned: some material may not suit children under 13.',
            'R': 'Restricted: under 17 only with a parent or guardian.',
            'NC17': 'Adults only: no one 17 or under.',
        }
        return descriptions[self.value]


class MovieQuerySet(models.QuerySet):
    def with_availability(self) -> 'MovieQuerySet':
        """
        Annotated with `total_copies` and `available_copies`, which a `MovieCard` shows. A copy is
        out while it has an open rental, and there's at most one per copy, so counting open
        rentals counts the copies that are out. A retired copy counts in neither.
        """
        in_rotation = Q(copies__retired_at__isnull=True)
        return self.annotate(
            total_copies=models.Count('copies', filter=in_rotation, distinct=True),
            copies_out=models.Count(
                'copies__rentals',
                filter=in_rotation & Q(copies__rentals__returned_at__isnull=True),
                distinct=True),
        ).annotate(available_copies=models.F('total_copies') - models.F('copies_out'))


class Movie(models.Model):
    title = models.CharField(max_length=200)
    year = models.PositiveSmallIntegerField()
    genre = models.CharField(max_length=20, choices=Genre.choices)
    rating = models.CharField(max_length=4, choices=MovieRating.choices)

    objects = MovieQuerySet.as_manager()

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f'{self.title} ({self.year})'


class CopyLabel:
    """What the label maker printed on a copy's case: four letters, a hyphen, four digits."""

    @staticmethod
    def generate(rng: random.Random | None = None) -> str:
        # The seed migration passes a seeded `rng`, so every migrate gives the same labels.
        rng = rng or random.SystemRandom()
        letters = ''.join(rng.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(4))
        digits = ''.join(rng.choice('0123456789') for _ in range(4))
        return f'{letters}-{digits}'


class CopyQuerySet(models.QuerySet):
    def create_copies(self, movie: Movie, count: int) -> list['Copy']:
        """
        `count` new copies of `movie`, each with a label no copy has. Sync, since it queries
        between generating and inserting; async code calls it through `sync_to_async`.
        """
        labels: set[str] = set()
        while len(labels) < count:
            candidates = {CopyLabel.generate() for _ in range(count - len(labels))} - labels
            taken = set(self.filter(label__in=candidates).values_list('label', flat=True))
            labels |= candidates - taken
        return self.bulk_create([Copy(movie=movie, label=label) for label in labels])


class Copy(models.Model):
    """One physical disc. Three copies of a movie are three rows."""

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='copies')
    # New copies get checked labels from create_copies(). The default covers a copy saved any
    # other way, such as from the admin, where a repeat is left to the unique column to refuse.
    label = models.SlugField(max_length=9, unique=True, editable=False, default=CopyLabel.generate)
    # When it went on the shelf, which the home page's new arrivals are picked by.
    added_at = models.DateTimeField(auto_now_add=True)
    # Out of rotation for good, after a report said it can't be recovered.
    retired_at = models.DateTimeField(null=True, blank=True)

    objects = CopyQuerySet.as_manager()

    class Meta:
        verbose_name_plural = 'copies'

    def __str__(self):
        return f'{self.movie.title}, copy {self.label}'


class Rental(models.Model):
    """
    Someone took a copy home. Open while `returned_at` is empty, so a copy with no open rental is
    on the shelf, and the returned rows are the history.
    """

    copy = models.ForeignKey(Copy, on_delete=models.CASCADE, related_name='rentals')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rentals')
    taken_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-taken_at']
        constraints = [
            # Two checkouts racing for the last copy can't both take it: the second insert fails.
            models.UniqueConstraint(
                fields=['copy'],
                condition=Q(returned_at__isnull=True),
                name='one_open_rental_per_copy'),
        ]

    def __str__(self):
        return f'{self.copy} with {self.user}'


class CopyReportKind(models.TextChoices):
    SCRATCHED = 'scratched', 'Scratched or skips'
    BROKEN_CASE = 'broken_case', 'Broken case'
    LOST = 'lost', 'Lost'
    OTHER = 'other', 'Something else'


class CopyReport(models.Model):
    """Someone with a copy out said something is wrong with it. Reports are history, never edited."""

    NOTES_MAX_LENGTH = 1000

    copy = models.ForeignKey(Copy, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='copy_reports')
    kind = models.CharField(max_length=20, choices=CopyReportKind.choices)
    notes = models.TextField(max_length=NOTES_MAX_LENGTH)
    # It can't come back into rotation, so the report retired the copy.
    unrecoverable = models.BooleanField(default=False)
    reported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reported_at']

    def __str__(self):
        return f'{self.copy}: {self.get_kind_display()}'
