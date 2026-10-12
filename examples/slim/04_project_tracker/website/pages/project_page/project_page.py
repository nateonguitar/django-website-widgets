from website_widgets import register_url

from website.access import UserAccessControl
from website.api.errors import ForbiddenException, NotFoundException
from website.models import Project
from website.pages.tracker_page import TrackerPage


@register_url('projects/<int:project_id>/')
class ProjectPage(TrackerPage):
    def __init__(self, project_id: int):
        super().__init__()
        self.project_id = project_id

    async def set_context(self):
        await super().set_context()
        viewer = UserAccessControl.require_user(self.viewer)
        project = await Project.objects.select_related('created_by').filter(pk=self.project_id).afirst()
        if project is None:
            raise NotFoundException()
        if not viewer.is_staff and project.created_by_id != viewer.pk:
            raise ForbiddenException()
        # The head comes from the project itself, so it is in the HTML a crawler receives.
        self.context.page['title'] = project.name
        self.context.page['description'] = project.meta_description
        self.context.data['project'] = project
        self.context.data['name_max_length'] = Project.NAME_MAX_LENGTH
        self.context.data['description_max_length'] = Project.DESCRIPTION_MAX_LENGTH
