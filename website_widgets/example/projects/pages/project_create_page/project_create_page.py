from website_widgets.example.projects.user_access_control import UserAccessControl
from website_widgets.example.projects.pages.projects_app_page.projects_app_page import ProjectsAppPage
from website_widgets.example.projects.store import Project


class ProjectCreatePage(ProjectsAppPage):
    def set_context(self):
        super().set_context()
        UserAccessControl.require_user(self.viewer)
        self.context.page['title'] = 'New project'
        self.context.page['description'] = 'Create a project in the example site.'
        self.context.data['name_max_length'] = Project.NAME_MAX_LENGTH
        self.context.data['description_max_length'] = Project.DESCRIPTION_MAX_LENGTH
