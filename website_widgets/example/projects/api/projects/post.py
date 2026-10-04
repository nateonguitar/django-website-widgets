from django.http import JsonResponse

from website_widgets.example.projects.api.projects.project_create_dto import ProjectCreateDto
from website_widgets.example.projects.api.projects.project_response_dto import ProjectResponseDto
from website_widgets.example.projects.api.projects_app_endpoint import ProjectsAppEndpoint
from website_widgets.example.projects.store import Project, Store
from website_widgets.example.projects.user_access_control import UserAccessControl


class ProjectsPostEndpoint(ProjectsAppEndpoint):
    """Creates a project owned by the viewer, the admin included."""

    method = 'POST'

    async def handle(self):
        viewer = UserAccessControl.require_user(self.viewer)
        request_data = self.read_json()
        dto = ProjectCreateDto.from_dict(request_data)
        dto.validate()
        project = Project.from_create_dto(dto, created_by=viewer)
        Store.add_project(project)
        response_dto = ProjectResponseDto.from_project(project)
        response_data = response_dto.to_dict()
        return JsonResponse(response_data, status=201)
