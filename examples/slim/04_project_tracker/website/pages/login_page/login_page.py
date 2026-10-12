from django.contrib.auth.models import User

from website_widgets import register_url

from website.pages.tracker_page import TrackerPage


@register_url('login/')
class LoginPage(TrackerPage):
    page_title = 'Log in'
    page_description = 'Log in to the tracker as one of three demo users.'

    async def set_context(self):
        await super().set_context()
        if self.viewer.is_authenticated:
            self.template_filename = 'login_page__already_logged_in.html'
            return
        self.context.data['users'] = [user async for user in User.objects.order_by('pk')]
        # Passed through as given; the login endpoint decides whether it is safe to follow.
        self.context.data['next'] = self.request.GET.get('next', '')
