from django.urls import path

from website_widgets.example.pages.caching_page.caching_page import CachingPage
from website_widgets.example.pages.index_page.index_page import ExampleIndexPage
from website_widgets.example.pages.simple_page.simple_page import SimplePage
from website_widgets.example.pages.widget_composition_page.widget_composition_page import WidgetCompositionPage
from website_widgets.example.pages.unwrapped_page.unwrapped_page import UnwrappedPage


urlpatterns = [
    path('',                    ExampleIndexPage.as_view(),          name='example_index'),
    path('simple/',             SimplePage.as_view(),                name='example_simple_page'),
    path('widget-composition/', WidgetCompositionPage.as_view(),     name='example_widget_composition_page'),
    path('unwrapped/',          UnwrappedPage.as_view(),             name='example_unwrapped_page'),
    path('caching/',            CachingPage.as_view(),               name='example_caching_page'),
]
