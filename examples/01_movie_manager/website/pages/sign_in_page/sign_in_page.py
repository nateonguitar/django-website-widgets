from django.shortcuts import redirect
from website_widgets import register_url

from website.exceptions import RedirectException
from website.pages.app_page import AppPage


@register_url('sign-in')
class SignInPage(AppPage):
    page_title = 'Sign in'

    async def set_context(self):
        if self.context.page['user'].is_authenticated:
            raise RedirectException(redirect('website:HomePage'))
        # Handed to the endpoint as it came, which follows it only to a path on this site.
        self.context.data['next'] = self.request.GET.get('next', '')
