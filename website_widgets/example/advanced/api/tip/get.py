import asyncio

from django.http import JsonResponse

from website_widgets.example.advanced.api.tip.tip_request_dto import TipRequestDto
from website_widgets.example.advanced.api.tip.tip_response_dto import TipResponseDto
from website_widgets.example.advanced.widgets.tip_card.tip_card import TipCard
from website_widgets.example.api.endpoint import Endpoint


class TipGetEndpoint(Endpoint):
    """
    Returns tip `?number=N` rendered on the server, for the page to add under the others: the
    pattern behind an infinite scroller or a "load more" button.
    """

    method = 'GET'
    MOCK_QUERY_SECONDS = 0.75

    async def handle(self):
        dto = TipRequestDto.from_query(self.request.GET)
        dto.validate()
        # Stands in for an awaited database query, long enough to watch the button wait for it.
        await asyncio.sleep(self.MOCK_QUERY_SECONDS)
        tip_card = TipCard(number=dto.number)
        html = await tip_card.render__standalone(self.request)
        response_dto = TipResponseDto(html=html)
        response_data = response_dto.to_dict()
        return JsonResponse(response_data)
