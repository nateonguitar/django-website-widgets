import dataclasses
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from django.urls import reverse

if TYPE_CHECKING:
    from website_widgets.example.projects.api.projects.by_id.project_update_dto import ProjectUpdateDto
    from website_widgets.example.projects.api.projects.project_create_dto import ProjectCreateDto


@dataclass(kw_only=True)
class User:
    id: int
    username: str
    name: str
    is_admin: bool = False


@dataclass(kw_only=True)
class Project:
    NAME_MAX_LENGTH = 100
    DESCRIPTION_MAX_LENGTH = 1000

    id: int | None = None
    name: str
    description: str = ''
    created_by: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_create_dto(cls, dto: 'ProjectCreateDto', created_by: User) -> 'Project':
        """An unsaved project, owned by `created_by`."""
        return cls(
            name=dto.name,
            description=dto.description,
            created_by=created_by.id)

    def updated_with(self, dto: 'ProjectUpdateDto') -> 'Project':
        """A copy with whichever fields `dto` holds, leaving this one unchanged."""
        return dataclasses.replace(
            self,
            name=self.name if dto.name is None else dto.name,
            description=self.description if dto.description is None else dto.description)

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

    def can_access(self, viewer: User | None) -> bool:
        """Viewing, editing and deleting all follow this one rule."""
        return viewer is not None and (viewer.is_admin or viewer.id == self.created_by)

    @property
    def creator(self) -> User | None:
        return Store.find_user(self.created_by)

    @property
    def created_by_name(self) -> str | None:
        creator = self.creator
        return creator.name if creator else None

    @property
    def url(self) -> str:
        return reverse('website_widgets_example_project', kwargs={'project_id': self.id})

    @property
    def meta_description(self) -> str:
        return self.description or f'The {self.name} project.'

    @property
    def updated_at_display(self) -> str:
        """Shared by the template and the JSON, so an in-place edit shows what a reload would."""
        return self.updated_at.strftime('%d %b %Y, %H:%M:%S UTC')


class Store:
    """
    The example site's database: plain Python lists in this process's memory.

    It is wiped whenever the Django server restarts, autoreloads included. Behind a load balancer,
    or with several server processes, each process holds its own copy, so what a request sees
    depends on which process serves it.
    """

    users: list[User] = []
    projects: list[Project] = []
    _last_project_id = 0

    @classmethod
    def reset(cls):
        now = datetime.now(timezone.utc)
        cls.users = [
            User(id=1, username='user_1', name='Riley Park'),
            User(id=2, username='user_2', name='Jordan Avery'),
            User(id=3, username='admin', name='Site Admin', is_admin=True),
        ]
        cls.projects = [
            Project(
                id=1,
                name='Garden planner',
                description='Which vegetables go in which bed, and when to plant them.',
                created_by=1,
                created_at=now,
                updated_at=now),
            Project(
                id=2,
                name='Reading list',
                description='Books to read this year, with a line on each one once finished.',
                created_by=2,
                created_at=now,
                updated_at=now),
        ]
        cls._last_project_id = 2

    @classmethod
    def find_user(cls, user_id: int | None) -> User | None:
        return next((user for user in cls.users if user.id == user_id), None)

    @classmethod
    def find_user_by_username(cls, username: str) -> User | None:
        return next((user for user in cls.users if user.username == username), None)

    @classmethod
    def find_project(cls, project_id: int) -> Project | None:
        return next((project for project in cls.projects if project.id == project_id), None)

    @classmethod
    def projects_for(cls, viewer: User) -> list[Project]:
        return [project for project in cls.projects if project.can_access(viewer)]

    @classmethod
    def add_project(cls, project: Project) -> Project:
        """Saves a validated project, giving it the next id and its timestamps."""
        now = datetime.now(timezone.utc)
        cls._last_project_id += 1
        project.id = cls._last_project_id
        project.created_at = now
        project.updated_at = now
        cls.projects.append(project)
        return project

    @classmethod
    def update_project(cls, project: Project) -> Project:
        """Saves a validated edit in place of the stored project with the same id."""
        project.updated_at = datetime.now(timezone.utc)
        index = next(index for index, stored in enumerate(cls.projects) if stored.id == project.id)
        cls.projects[index] = project
        return project

    @classmethod
    def delete_project(cls, project: Project):
        cls.projects.remove(project)
