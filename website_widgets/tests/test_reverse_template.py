from django.test import SimpleTestCase, override_settings
from django.test.utils import override_script_prefix
from django.urls import NoReverseMatch, reverse

from website_widgets import reverse_template


@override_settings(ROOT_URLCONF='website_widgets.tests.urls')
class ReverseTemplateTestCase(SimpleTestCase):
    def test_reverse_template__returns_reverse_result__when_route_has_no_parameters(self):
        url_template = reverse_template('plain')

        expected_url = reverse('plain')
        self.assertEqual(url_template, expected_url)

    def test_reverse_template__returns_route_parameter_names__when_param_names_omitted(self):
        url_template = reverse_template('comment')

        self.assertEqual(url_template, '/posts/{post_id}/comments/{comment_id}')

    def test_reverse_template__returns_template__when_parameter_not_after_slash(self):
        url_template = reverse_template('file')

        self.assertEqual(url_template, '/files/file-{file_id}')

    def test_reverse_template__keeps_literal_segment__when_route_contains_slash_one(self):
        url_template = reverse_template('literal_one')

        self.assertEqual(url_template, '/v1/1/{item_id}')

    def test_reverse_template__returns_every_placeholder__when_route_has_eleven_parameters(self):
        placeholders = [
            '{p' + str(index) + '}'
            for index in range(11)
        ]
        expected = '/' + '/'.join(placeholders)

        url_template = reverse_template('eleven')

        self.assertEqual(url_template, expected)

    def test_reverse_template__returns_template__when_converters_reject_digits(self):
        url_template = reverse_template('converters')

        self.assertEqual(url_template, '/things/{thing_id}/{thing_slug}/{rest}')

    def test_reverse_template__includes_prefix__when_route_is_included(self):
        url_template = reverse_template('section_page')

        self.assertEqual(url_template, '/section/pages/{page_id}')

    def test_reverse_template__includes_prefix__when_name_is_namespaced(self):
        url_template = reverse_template('outer:post')

        self.assertEqual(url_template, '/outer/posts/{post_id}')

    def test_reverse_template__includes_every_prefix__when_namespaces_are_nested(self):
        url_template = reverse_template('outer:inner:item')

        self.assertEqual(url_template, '/outer/nested/items/{item_id}')

    def test_reverse_template__uses_default_instance__when_name_uses_app_namespace(self):
        url = reverse('outer_app:post', args=[1])
        url_template = reverse_template('outer_app:post')

        self.assertEqual(url, '/app-default/posts/1')
        self.assertEqual(url_template, '/app-default/posts/{post_id}')

    def test_reverse_template__includes_script_prefix__when_one_is_set(self):
        with override_script_prefix('/mounted/'):
            url_template = reverse_template('outer:post')

        self.assertEqual(url_template, '/mounted/outer/posts/{post_id}')

    def test_reverse_template__renames_placeholders_in_order__when_param_names_given(self):
        url_template = reverse_template('comment', ['a', 'b'])

        self.assertEqual(url_template, '/posts/{a}/comments/{b}')

    def test_reverse_template__names_unnamed_group__when_param_names_given(self):
        url_template = reverse_template('unnamed_group', ['legacy_id'])

        self.assertEqual(url_template, '/legacy/{legacy_id}/')

    def test_reverse_template__chooses_route_by_parameter_count__when_param_names_given(self):
        url_template = reverse_template('optional_group', ['page'])

        self.assertEqual(url_template, '/optional/{page}/')

    def test_reverse_template__fails__when_routes_for_name_differ_in_parameters(self):
        with self.assertRaises(ValueError):
            reverse_template('optional_group')

    def test_reverse_template__fails__when_param_names_count_differs_from_route(self):
        with self.assertRaises(NoReverseMatch):
            reverse_template('comment', ['post_id'])

    def test_reverse_template__fails__when_name_is_unknown(self):
        with self.assertRaises(NoReverseMatch):
            reverse_template('missing')

    def test_reverse_template__fails__when_namespace_is_unknown(self):
        with self.assertRaises(NoReverseMatch):
            reverse_template('missing:post')
