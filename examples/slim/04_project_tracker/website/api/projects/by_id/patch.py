from dataclasses import dataclass

from django.http import JsonResponse

from website.access import UserAccessControl
from website.api.endpoint import Endpoint
from website.api.errors import ForbiddenException, NotFoundException, UnprocessableEntityException
from website.api.projects.project_response_dto import ProjectResponseDto
from website.models import Project


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


class ProjectPatchEndpoint(Endpoint):
    """Updates whichever of name and description the body includes. A plain HTML form can't send `PATCH`."""

    method = 'PATCH'

    async def handle(self, project_id: int):
        viewer = UserAccessControl.require_user(await self.get_viewer())
        project = await Project.objects.select_related('created_by').filter(pk=project_id).afirst()
        if project is None:
            raise NotFoundException()
        if not viewer.is_staff and project.created_by_id != viewer.pk:
            raise ForbiddenException()
        request_data = self.read_json()
        dto = ProjectUpdateDto.from_dict(request_data)
        dto.validate()
        self._update_project_from_dto(project, dto)
        await project.asave()
        response_dto = ProjectResponseDto.from_project(project)
        response_data = response_dto.to_dict()
        return JsonResponse(response_data)

    @staticmethod
    def _update_project_from_dto(project: Project, dto: ProjectUpdateDto):
        """Sets whichever fields the update holds, unsaved."""
        if dto.name is not None:
            project.name = dto.name
        if dto.description is not None:
            project.description = dto.description
