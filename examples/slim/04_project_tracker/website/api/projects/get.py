from django.http import JsonResponse

from website.access import UserAccessControl
from website.api.endpoint import Endpoint
from website.api.projects.project_response_dto import ProjectResponseDto
from website.models import Project


class ProjectsGetEndpoint(Endpoint):
    """The projects the viewer can access: their own, or every project for staff."""

    method = 'GET'

    async def handle(self):
        viewer = UserAccessControl.require_user(await self.get_viewer())
        projects = Project.objects.select_related('created_by')
        if not viewer.is_staff:
            projects = projects.filter(created_by=viewer)
        response_dtos = [
            ProjectResponseDto.from_project(project)
            async for project in projects
        ]
        response_data = [dto.to_dict() for dto in response_dtos]
        return JsonResponse(response_data, safe=False)
