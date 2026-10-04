from django.urls import include, path

from website_widgets.example.index.pages.index_page.index_page import IndexPage


urlpatterns = [
    path('',            IndexPage.as_view(),                     name='website_widgets_example_index'),
    path('projects/',   include('website_widgets.example.projects.urls')),
    path('advanced/',   include('website_widgets.example.advanced.urls')),
]
