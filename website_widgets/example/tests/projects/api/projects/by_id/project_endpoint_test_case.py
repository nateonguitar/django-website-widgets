from django.urls import reverse

from website_widgets.example.tests.example_test_case import ExampleTestCase


class ProjectEndpointTestCase(ExampleTestCase):
    """URL helpers shared by the tests of the endpoints on `api/projects/<id>/`."""

    def project_url(self, project_id: int) -> str:
        return reverse('website_widgets_example_api_project', kwargs={'project_id': project_id})

    def page_url(self, project_id: int) -> str:
        return reverse('website_widgets_example_project', kwargs={'project_id': project_id})
