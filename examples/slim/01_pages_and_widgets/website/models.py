from django.db import models


class Book(models.Model):
    """What the async pages query. Seeded by a data migration, so `migrate` gives a full shelf."""

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    year = models.PositiveIntegerField()

    class Meta:
        ordering = ['year']

    def __str__(self):
        return self.title
