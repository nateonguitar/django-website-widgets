import dataclasses
from dataclasses import dataclass

from website.models import Project


@dataclass(kw_only=True)
class ProjectResponseDto:
    """A project as every project endpoint returns it. Needs `created_by` already loaded."""

    id: int
    name: str
    description: str
    created_by: int
    created_by_name: str
    created_at: str
    updated_at: str
    updated_at_display: str
    meta_description: str
    url: str

    @classmethod
    def from_project(cls, project: Project) -> 'ProjectResponseDto':
        creator = project.created_by
        return cls(
            id=project.pk,
            name=project.name,
            description=project.description,
            created_by=creator.pk,
            created_by_name=creator.get_full_name() or creator.username,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
            updated_at_display=project.updated_at_display,
            meta_description=project.meta_description,
            url=project.url)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)
