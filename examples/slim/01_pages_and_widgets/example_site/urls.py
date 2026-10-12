from django.urls import path

from website_widgets import PageRoutes


urlpatterns = [
    # Every page under website/pages/ with @register_url.
    path('', PageRoutes.urls()),
]
