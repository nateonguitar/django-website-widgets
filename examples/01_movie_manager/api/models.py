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


class MovieQuerySet(models.QuerySet):
    def with_availability(self) -> 'MovieQuerySet':
        """
        Annotated with `total_copies` and `available_copies`, which a `MovieCard` shows. A copy is
        out while it has an open rental, and there's at most one per copy, so counting open
        rentals counts the copies that are out.
        """
        return self.annotate(
            total_copies=models.Count('copies', distinct=True),
            copies_out=models.Count(
                'copies__rentals',
                filter=Q(copies__rentals__returned_at__isnull=True),
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


class Copy(models.Model):
    """One physical disc. Three copies of a movie are three rows."""

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='copies')
    # When it went on the shelf, which the home page's new arrivals are picked by.
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'copies'

    def __str__(self):
        return f'{self.movie.title}, copy {self.pk}'


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
