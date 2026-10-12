from django.contrib.auth import alogout
from django.http import JsonResponse

from website.api.endpoint import Endpoint


class LogoutPostEndpoint(Endpoint):
    method = 'POST'

    async def handle(self):
        await alogout(self.request)
        response_data = {'logged_out': True}
        return JsonResponse(response_data)
