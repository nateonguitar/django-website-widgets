from django.http import HttpResponse

from website_widgets.example.api.errors import ForbiddenException, NotFoundException
from website_widgets.example.projects.api.projects_app_endpoint import ProjectsAppEndpoint
from website_widgets.example.projects.store import Store
from website_widgets.example.projects.user_access_control import UserAccessControl


class ProjectDeleteEndpoint(ProjectsAppEndpoint):
    """A plain HTML form can't send `DELETE`."""

    method = 'DELETE'

    async def handle(self, project_id: int):
        viewer = UserAccessControl.require_user(self.viewer)
        project = Store.find_project(project_id)
        if project is None:
            raise NotFoundException()
        if not project.can_access(viewer):
            raise ForbiddenException()
        Store.delete_project(project)
        return HttpResponse(status=204)
