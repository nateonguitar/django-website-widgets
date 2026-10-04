from dataclasses import dataclass

from website_widgets.example.api.errors import UnprocessableEntityException
from website_widgets.example.projects.store import Project


@dataclass(kw_only=True)
class ProjectUpdateDto:
    """The update endpoint's body. A field left out, or sent as `null`, keeps its current value."""

    name: str | None = None
    description: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> 'ProjectUpdateDto':
        return cls(
            name=data.get('name'),
            description=data.get('description'))

    def validate(self):
        errors = {}
        if self.name is not None:
            if name_errors := Project.name_errors(self.name):
                errors['name'] = name_errors
        if self.description is not None:
            if description_errors := Project.description_errors(self.description):
                errors['description'] = description_errors
        if errors:
            raise UnprocessableEntityException(errors)
