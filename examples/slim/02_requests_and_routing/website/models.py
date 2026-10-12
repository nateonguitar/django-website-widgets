from django.db import models


class Article(models.Model):
    """What the pages show. Seeded by a data migration, with two seeded users to log in as."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    summary = models.CharField(max_length=300)
    body = models.TextField()
    # Readable only when logged in; anyone else gets the page's 401 variant.
    members_only = models.BooleanField(default=False)
    published_at = models.DateTimeField()
    # The changelog page's ETag is built from the newest of these.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title
