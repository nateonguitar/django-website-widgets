from website_widgets import register_url

from website.access import UserAccessControl
from website.models import Project
from website.pages.tracker_page import TrackerPage
from website.widgets.project_list_tile.project_list_tile import ProjectListTile


@register_url('')
class ProjectsPage(TrackerPage):
    async def set_context(self):
        await super().set_context()
        viewer = UserAccessControl.require_user(self.viewer)
        self.context.page['title'] = 'All projects' if viewer.is_staff else 'Your projects'
        self.context.page['description'] = 'Projects in the tracker, one tile each.'
        projects = Project.objects.select_related('created_by')
        if not viewer.is_staff:
            projects = projects.filter(created_by=viewer)
        self.context.children['tiles'] = [
            ProjectListTile(project=project)
            async for project in projects
        ]
