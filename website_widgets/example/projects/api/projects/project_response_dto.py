import dataclasses
from dataclasses import dataclass

from website_widgets.example.projects.store import Project


@dataclass(kw_only=True)
class ProjectResponseDto:
    """A project as every project endpoint returns it."""

    id: int
    name: str
    description: str
    created_by: int
    created_by_name: str | None
    created_at: str
    updated_at: str
    updated_at_display: str
    meta_description: str
    url: str

    @classmethod
    def from_project(cls, project: Project) -> 'ProjectResponseDto':
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            created_by=project.created_by,
            created_by_name=project.created_by_name,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
            updated_at_display=project.updated_at_display,
            meta_description=project.meta_description,
            url=project.url)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)
