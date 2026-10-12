from django.contrib.auth.models import User
from django.db.models import Count

from website_widgets import register_url

from website.access import UserAccessControl
from website.pages.tracker_page import TrackerPage


@register_url('team/')
class TeamPage(TrackerPage):
    """Staff only. The check runs before any data is loaded."""

    page_title = 'Team'
    page_description = 'Everyone in the tracker.'

    async def set_context(self):
        await super().set_context()
        UserAccessControl.require_staff(self.viewer)
        users = User.objects.annotate(project_count=Count('projects')).order_by('pk')
        self.context.data['users'] = [user async for user in users]
