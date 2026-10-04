from website_widgets.example.projects.user_access_control import UserAccessControl
from website_widgets.example.projects.pages.projects_app_page.projects_app_page import ProjectsAppPage
from website_widgets.example.projects.store import Store
from website_widgets.example.projects.widgets.project_list_tile.project_list_tile import ProjectListTile


class ProjectsPage(ProjectsAppPage):
    def set_context(self):
        super().set_context()
        viewer = UserAccessControl.require_user(self.viewer)
        self.context.page['title'] = 'All projects' if viewer.is_admin else 'Your projects'
        self.context.page['description'] = 'Projects in the example site, one tile each.'
        self.context.children['tiles'] = [
            ProjectListTile(project=project) for project in Store.projects_for(viewer)
        ]
