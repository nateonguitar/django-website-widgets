from website_widgets.example.projects.pages.projects_app_page.projects_app_page import ProjectsAppPage
from website_widgets.example.projects.store import Store


class LoginPage(ProjectsAppPage):
    def set_context(self):
        super().set_context()
        self.context.page['title'] = 'Log in'
        self.context.page['description'] = 'Log in to the example site as one of three demo users.'
        if self.viewer is not None:
            self.template_filename = 'login_page__already_logged_in.html'
            return
        self.context.data['users'] = Store.users
        # Passed through as given; the login endpoint decides whether it is safe to follow.
        self.context.data['next'] = self.request.GET.get('next', '')
