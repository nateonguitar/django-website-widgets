from dataclasses import dataclass

from django.http import JsonResponse

from website.access import UserAccessControl
from website.api.endpoint import Endpoint
from website.api.errors import UnprocessableEntityException
from website.api.projects.project_response_dto import ProjectResponseDto
from website.models import Project


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


class ProjectsPostEndpoint(Endpoint):
    """Creates a project owned by the viewer, staff included."""

    method = 'POST'

    async def handle(self):
        viewer = UserAccessControl.require_user(await self.get_viewer())
        request_data = self.read_json()
        dto = ProjectCreateDto.from_dict(request_data)
        dto.validate()
        project = await Project.objects.acreate(
            name=dto.name,
            description=dto.description,
            created_by=viewer)
        response_dto = ProjectResponseDto.from_project(project)
        response_data = response_dto.to_dict()
        return JsonResponse(response_data, status=201)
