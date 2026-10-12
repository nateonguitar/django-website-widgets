from django.conf import settings
from django.db import models
from django.urls import reverse


class Project(models.Model):
    """
    A project, owned by the user who created it. Every query that a template will read
    `created_by` from uses `select_related('created_by')`: following the foreign key lazily in a
    template would run a synchronous query inside the async page.
    """

    NAME_MAX_LENGTH = 100
    DESCRIPTION_MAX_LENGTH = 1000

    name = models.CharField(max_length=NAME_MAX_LENGTH)
    description = models.TextField(max_length=DESCRIPTION_MAX_LENGTH, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @classmethod
    def name_errors(cls, name) -> list[str]:
        """The rules for a name, shared by the create and update DTOs."""
        if not name:
            return ['The name is required.']
        if not isinstance(name, str):
            return ['The name must be text.']
        if len(name) > cls.NAME_MAX_LENGTH:
            return [f'Keep the name to {cls.NAME_MAX_LENGTH} characters or fewer.']
        return []

    @classmethod
    def description_errors(cls, description) -> list[str]:
        """The rules for a description, shared by the create and update DTOs."""
        if not isinstance(description, str):
            return ['The description must be text.']
        if len(description) > cls.DESCRIPTION_MAX_LENGTH:
            return [f'Keep the description to {cls.DESCRIPTION_MAX_LENGTH:,} characters or fewer.']
        return []

    @property
    def url(self) -> str:
        return reverse('website:ProjectPage', kwargs={'project_id': self.pk})

    @property
    def meta_description(self) -> str:
        return self.description or f'The {self.name} project.'

    @property
    def updated_at_display(self) -> str:
        """Shared by the template and the JSON, so an in-place edit shows what a reload would."""
        return self.updated_at.strftime('%d %b %Y, %H:%M:%S UTC')
