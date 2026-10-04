from dataclasses import dataclass

from website_widgets.example.api.errors import UnprocessableEntityException
from website_widgets.example.projects.store import Project


@dataclass(kw_only=True)
class ProjectCreateDto:
    """The create endpoint's body. Only the fields a client may set; the owner is the viewer."""

    name: str
    description: str = ''

    @classmethod
    def from_dict(cls, data: dict) -> 'ProjectCreateDto':
        return cls(
            name=data.get('name'),
            description=data.get('description', ''))

    def validate(self):
        errors = {}
        if name_errors := Project.name_errors(self.name):
            errors['name'] = name_errors
        if description_errors := Project.description_errors(self.description):
            errors['description'] = description_errors
        if errors:
            raise UnprocessableEntityException(errors)
