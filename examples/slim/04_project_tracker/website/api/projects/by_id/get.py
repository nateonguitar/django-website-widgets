from django.http import JsonResponse

from website.access import UserAccessControl
from website.api.endpoint import Endpoint
from website.api.errors import ForbiddenException, NotFoundException
from website.api.projects.project_response_dto import ProjectResponseDto
from website.models import Project


class ProjectGetEndpoint(Endpoint):
    method = 'GET'

    async def handle(self, project_id: int):
        viewer = UserAccessControl.require_user(await self.get_viewer())
        project = await Project.objects.select_related('created_by').filter(pk=project_id).afirst()
        if project is None:
            raise NotFoundException()
        if not viewer.is_staff and project.created_by_id != viewer.pk:
            raise ForbiddenException()
        response_dto = ProjectResponseDto.from_project(project)
        response_data = response_dto.to_dict()
        return JsonResponse(response_data)
