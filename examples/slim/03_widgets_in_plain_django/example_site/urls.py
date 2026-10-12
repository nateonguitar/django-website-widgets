from django.urls import path

from website.example_admin_site import example_admin_site
from website.views.upcoming_events_view import UpcomingEventsView


# No PageRoutes include: nothing in this example is a WebPage.
urlpatterns = [
    path('admin/', example_admin_site.urls),
    path('', UpcomingEventsView.as_view(), name='upcoming_events'),
]
