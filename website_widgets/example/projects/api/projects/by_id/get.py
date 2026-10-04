from django.http import JsonResponse

from website_widgets.example.api.errors import ForbiddenException, NotFoundException
from website_widgets.example.projects.api.projects.project_response_dto import ProjectResponseDto
from website_widgets.example.projects.api.projects_app_endpoint import ProjectsAppEndpoint
from website_widgets.example.projects.store import Store
from website_widgets.example.projects.user_access_control import UserAccessControl


class ProjectGetEndpoint(ProjectsAppEndpoint):
    method = 'GET'

    async def handle(self, project_id: int):
        viewer = UserAccessControl.require_user(self.viewer)
        project = Store.find_project(project_id)
        if project is None:
            raise NotFoundException()
        if not project.can_access(viewer):
            raise ForbiddenException()
        response_dto = ProjectResponseDto.from_project(project)
        response_data = response_dto.to_dict()
        return JsonResponse(response_data)
