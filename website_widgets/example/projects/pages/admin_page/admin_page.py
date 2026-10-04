from website_widgets.example.projects.user_access_control import UserAccessControl
from website_widgets.example.projects.pages.projects_app_page.projects_app_page import ProjectsAppPage
from website_widgets.example.projects.store import Store


class AdminPage(ProjectsAppPage):
    def set_context(self):
        super().set_context()
        UserAccessControl.require_admin_user(self.viewer)
        self.context.page['title'] = 'Admin'
        self.context.page['description'] = 'Every user in the example site.'
        self.context.data['users'] = [
            {
                'user': user,
                'project_count': sum(
                    1 for project in Store.projects if project.created_by == user.id),
            }
            for user in Store.users
        ]
