from django.db import models


class Event(models.Model):
    """What every view, the email and the admin show. Seeded by a data migration."""

    name = models.CharField(max_length=200)
    starts_at = models.DateTimeField()
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['starts_at']

    def __str__(self):
        return self.name
