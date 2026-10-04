from django.urls import path

from website_widgets.example.advanced.api.tip.get import TipGetEndpoint
from website_widgets.example.advanced.pages.advanced_index_page.advanced_index_page import AdvancedIndexPage
from website_widgets.example.advanced.pages.async_page.async_page import AsyncPage
from website_widgets.example.advanced.pages.composition_page.composition_page import CompositionPage
from website_widgets.example.advanced.pages.conditional_page.conditional_page import ConditionalPage
from website_widgets.example.advanced.pages.widget_from_endpoint_page.widget_from_endpoint_page import WidgetFromEndpointPage
from website_widgets.example.api.endpoint import Endpoint


urlpatterns = [
    path('',                        AdvancedIndexPage.as_view(),          name='website_widgets_example_advanced'),
    path('composition/',            CompositionPage.as_view(),            name='website_widgets_example_composition'),
    path('async/',                  AsyncPage.as_view(),                  name='website_widgets_example_async'),
    path('widget-from-endpoint/',   WidgetFromEndpointPage.as_view(),     name='website_widgets_example_widget_from_endpoint'),
    path('conditional/',            ConditionalPage.as_view(),            name='website_widgets_example_conditional'),

    path(
        'api/tip/',
        Endpoint.route(TipGetEndpoint),
        name='website_widgets_example_api_tip'),
]
