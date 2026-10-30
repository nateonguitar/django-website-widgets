from django.urls import path

from website_widgets import PageRoutes


# Included from the project's urls.py: path('', include('website.urls')).
urlpatterns = [
    # Every page with @register_url under pages/, reversed as 'website:<name>'.
    path('', PageRoutes.urls()),
]
