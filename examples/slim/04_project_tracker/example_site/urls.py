from django.urls import path

from website_widgets import PageRoutes

from website.api.endpoint import Endpoint
from website.api.login.post import LoginPostEndpoint
from website.api.logout.post import LogoutPostEndpoint
from website.api.projects.by_id.delete import ProjectDeleteEndpoint
from website.api.projects.by_id.get import ProjectGetEndpoint
from website.api.projects.by_id.patch import ProjectPatchEndpoint
from website.api.projects.get import ProjectsGetEndpoint
from website.api.projects.post import ProjectsPostEndpoint


urlpatterns = [
    # Every page under website/pages/ with @register_url, reversed as website:<name>.
    path('', PageRoutes.urls()),

    # The JSON endpoints the pages' scripts call, one class per method, routed by URL.
    path(
        'api/login/',
        Endpoint.route(LoginPostEndpoint),
        name='api_login'),
    path(
        'api/logout/',
        Endpoint.route(LogoutPostEndpoint),
        name='api_logout'),
    path(
        'api/projects/',
        Endpoint.route(
            ProjectsGetEndpoint,
            ProjectsPostEndpoint),
        name='api_projects'),
    path(
        'api/projects/<int:project_id>/',
        Endpoint.route(
            ProjectGetEndpoint,
            ProjectPatchEndpoint,
            ProjectDeleteEndpoint),
        name='api_project'),
]
