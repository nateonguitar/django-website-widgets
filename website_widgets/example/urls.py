from django.urls import path

from website_widgets.example.pages.caching_page.caching_page import CachingPage
from website_widgets.example.pages.index_page.index_page import ExampleIndexPage
from website_widgets.example.pages.simple_page.simple_page import SimplePage
from website_widgets.example.pages.widget_composition_page.widget_composition_page import WidgetCompositionPage
from website_widgets.example.pages.unwrapped_page.unwrapped_page import UnwrappedPage


urlpatterns = [
    path('',                    ExampleIndexPage().render_page,      name='example_index'),
    path('simple/',             SimplePage().render_page,            name='example_simple_page'),
    path('widget-composition/', WidgetCompositionPage().render_page, name='example_widget_composition_page'),
    path('unwrapped/',          UnwrappedPage().render_page,         name='example_unwrapped_page'),
    path('caching/',            CachingPage().render_page,           name='example_caching_page'),
]
