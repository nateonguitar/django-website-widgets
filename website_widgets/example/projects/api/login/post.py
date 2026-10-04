from django.http import JsonResponse
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from website_widgets.example.api.errors import UnprocessableEntityException
from website_widgets.example.projects.api.login.login_request_dto import LoginRequestDto
from website_widgets.example.projects.api.login.login_response_dto import LoginResponseDto
from website_widgets.example.projects.api.login.user_response_dto import UserResponseDto
from website_widgets.example.projects.api.projects_app_endpoint import ProjectsAppEndpoint
from website_widgets.example.projects.store import Store
from website_widgets.example.projects.viewer_cookie import ViewerCookie


class LoginPostEndpoint(ProjectsAppEndpoint):
    """Logs in by username alone; any password is accepted. See `ViewerCookie`."""

    method = 'POST'

    async def handle(self):
        request_data = self.read_json()
        dto = LoginRequestDto.from_dict(request_data)
        dto.validate()
        user = Store.find_user_by_username(dto.username)
        if user is None:
            raise UnprocessableEntityException(errors={
                'username': ['No such user.'],
            })
        user_dto = UserResponseDto.from_user(user)
        next_url = self._safe_next(dto.next)
        response_dto = LoginResponseDto(
            user=user_dto,
            next=next_url)
        response_data = response_dto.to_dict()
        response = JsonResponse(response_data)
        ViewerCookie.set(response, user)
        return response

    @staticmethod
    def _safe_next(next_url: str) -> str:
        """Only a path on this site, so the login can't be used to send someone elsewhere."""
        if next_url.startswith('/') and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
            return next_url
        return reverse('website_widgets_example_projects')
