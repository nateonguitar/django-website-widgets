from django.http import HttpResponse

from website.access import UserAccessControl
from website.api.endpoint import Endpoint
from website.api.errors import ForbiddenException, NotFoundException
from website.models import Project


class ProjectDeleteEndpoint(Endpoint):
    """A plain HTML form can't send `DELETE`."""

    method = 'DELETE'

    async def handle(self, project_id: int):
        viewer = UserAccessControl.require_user(await self.get_viewer())
        project = await Project.objects.filter(pk=project_id).afirst()
        if project is None:
            raise NotFoundException()
        if not viewer.is_staff and project.created_by_id != viewer.pk:
            raise ForbiddenException()
        await project.adelete()
        return HttpResponse(status=204)
