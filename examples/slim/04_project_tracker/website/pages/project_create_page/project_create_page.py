from website_widgets import register_url

from website.access import UserAccessControl
from website.models import Project
from website.pages.tracker_page import TrackerPage


@register_url('projects/new/')
class ProjectCreatePage(TrackerPage):
    page_title = 'New project'
    page_description = 'Create a project in the tracker.'

    async def set_context(self):
        await super().set_context()
        UserAccessControl.require_user(self.viewer)
        self.context.data['name_max_length'] = Project.NAME_MAX_LENGTH
        self.context.data['description_max_length'] = Project.DESCRIPTION_MAX_LENGTH
