from django.http import JsonResponse

from website_widgets.example.projects.api.projects.project_response_dto import ProjectResponseDto
from website_widgets.example.projects.api.projects_app_endpoint import ProjectsAppEndpoint
from website_widgets.example.projects.store import Store
from website_widgets.example.projects.user_access_control import UserAccessControl


class ProjectsGetEndpoint(ProjectsAppEndpoint):
    """The projects the viewer can access: their own, or every project for the admin."""

    method = 'GET'

    async def handle(self):
        viewer = UserAccessControl.require_user(self.viewer)
        response_dtos = [
            ProjectResponseDto.from_project(project)
            for project in Store.projects_for(viewer)
        ]
        response_data = [dto.to_dict() for dto in response_dtos]
        return JsonResponse(response_data, safe=False)
