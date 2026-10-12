from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.urls import path

from website.models import Event
from website.views.events_admin_tool_view import EventsAdminToolView


class ExampleAdminSite(admin.AdminSite):
    """The admin, with a tool page beside the model admins, linked from its index."""

    index_template = 'admin/website/index.html'

    def get_urls(self):
        tool_view = EventsAdminToolView.as_view(admin_site=self)
        tool_urls = [
            path('tools/events/', self.admin_view(tool_view), name='events_tool'),
        ]
        return tool_urls + super().get_urls()


class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'starts_at', 'location']
    search_fields = ['name', 'location']


example_admin_site = ExampleAdminSite()
example_admin_site.register(Event, EventAdmin)
example_admin_site.register(User, UserAdmin)
example_admin_site.register(Group, GroupAdmin)
