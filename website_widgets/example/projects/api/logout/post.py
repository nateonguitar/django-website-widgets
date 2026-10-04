from django.http import JsonResponse

from website_widgets.example.projects.api.projects_app_endpoint import ProjectsAppEndpoint
from website_widgets.example.projects.viewer_cookie import ViewerCookie


class LogoutPostEndpoint(ProjectsAppEndpoint):
    method = 'POST'

    async def handle(self):
        response_data = {'logged_out': True}
        response = JsonResponse(response_data)
        ViewerCookie.clear(response)
        return response
