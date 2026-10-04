from django.urls import reverse

from website_widgets.example.tests.example_test_case import ExampleTestCase


class EndpointRouteTestCase(ExampleTestCase):
    """`Endpoint.route()`, exercised through the projects URL it routes GET and POST on."""

    def test_route__fails_listing_allowed_methods__when_no_endpoint_for_method(self):
        response = self.client.put(reverse('website_widgets_example_api_projects'))

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response['Allow'], 'GET, POST')
        self.assertIn('error', response.json())

    def test_route__fails_with_error_shape__when_body_not_json(self):
        self.log_in_as(self.USER_1)

        response = self.client.post(
            reverse('website_widgets_example_api_projects'),
            data='not json',
            content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'The request body must be JSON.'})

    def test_route__fails_with_422_listing_errors_by_field__when_unprocessable_entity_raised(self):
        self.log_in_as(self.USER_1)

        response = self.send_json('post', reverse('website_widgets_example_api_projects'), {
            'name': '',
            'description': 7,
        })

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {
            'errors': {
                'name': ['The name is required.'],
                'description': ['The description must be text.'],
            },
        })
