from website_widgets.example.api.errors import ForbiddenException, NotFoundException
from website_widgets.example.projects.pages.projects_app_page.projects_app_page import ProjectsAppPage
from website_widgets.example.projects.store import Project, Store
from website_widgets.example.projects.user_access_control import UserAccessControl


class ProjectPage(ProjectsAppPage):
    def __init__(self, project_id: int):
        super().__init__()
        self.project_id = project_id

    def set_context(self):
        super().set_context()
        viewer = UserAccessControl.require_user(self.viewer)
        project = Store.find_project(self.project_id)
        if project is None:
            raise NotFoundException()
        if not project.can_access(viewer):
            raise ForbiddenException()
        # The head comes from the project itself, so it is in the HTML a crawler receives.
        self.context.page['title'] = project.name
        self.context.page['description'] = project.meta_description
        self.context.data['project'] = project
        self.context.data['name_max_length'] = Project.NAME_MAX_LENGTH
        self.context.data['description_max_length'] = Project.DESCRIPTION_MAX_LENGTH
