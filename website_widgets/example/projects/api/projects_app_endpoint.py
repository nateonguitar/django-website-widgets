from django.http import HttpRequest

from website_widgets.example.api.endpoint import Endpoint
from website_widgets.example.projects.viewer_cookie import ViewerCookie


class ProjectsAppEndpoint(Endpoint):
    """The projects app's endpoints, which know who is logged in."""

    def __init__(self, request: HttpRequest):
        super().__init__(request)
        self.viewer = ViewerCookie.viewer(request)
