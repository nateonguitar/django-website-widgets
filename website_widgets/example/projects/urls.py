from django.urls import path

from website_widgets.example.api.endpoint import Endpoint
from website_widgets.example.projects.api.login.post import LoginPostEndpoint
from website_widgets.example.projects.api.logout.post import LogoutPostEndpoint
from website_widgets.example.projects.api.projects.by_id.delete import ProjectDeleteEndpoint
from website_widgets.example.projects.api.projects.by_id.get import ProjectGetEndpoint
from website_widgets.example.projects.api.projects.by_id.patch import ProjectPatchEndpoint
from website_widgets.example.projects.api.projects.get import ProjectsGetEndpoint
from website_widgets.example.projects.api.projects.post import ProjectsPostEndpoint
from website_widgets.example.projects.pages.admin_page.admin_page import AdminPage
from website_widgets.example.projects.pages.login_page.login_page import LoginPage
from website_widgets.example.projects.pages.project_create_page.project_create_page import ProjectCreatePage
from website_widgets.example.projects.pages.project_page.project_page import ProjectPage
from website_widgets.example.projects.pages.projects_page.projects_page import ProjectsPage


urlpatterns = [
    path('',                       ProjectsPage.as_view(),           name='website_widgets_example_projects'),
    path('login/',                 LoginPage.as_view(),              name='website_widgets_example_login'),
    path('new/',                   ProjectCreatePage.as_view(),      name='website_widgets_example_project_create'),
    path('<int:project_id>/',      ProjectPage.as_view(),            name='website_widgets_example_project'),
    path('admin/',                 AdminPage.as_view(),              name='website_widgets_example_admin'),

    path(
        'api/login/',
        Endpoint.route(
            LoginPostEndpoint),
        name='website_widgets_example_api_login'),
    path(
        'api/logout/',
        Endpoint.route(
            LogoutPostEndpoint),
        name='website_widgets_example_api_logout'),
    path(
        'api/projects/',
        Endpoint.route(
            ProjectsGetEndpoint,
            ProjectsPostEndpoint),
        name='website_widgets_example_api_projects'),
    path(
        'api/projects/<int:project_id>/',
        Endpoint.route(
            ProjectGetEndpoint,
            ProjectPatchEndpoint,
            ProjectDeleteEndpoint),
        name='website_widgets_example_api_project'),
]
