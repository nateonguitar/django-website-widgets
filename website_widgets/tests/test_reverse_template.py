from django.test import SimpleTestCase, override_settings
from django.test.utils import override_script_prefix
from django.urls import NoReverseMatch, reverse

from website_widgets import reverse_template


@override_settings(ROOT_URLCONF='website_widgets.tests.urls')
class ReverseTemplateTestCase(SimpleTestCase):
    def test_reverse_template__returns_reverse_result__when_route_has_no_parameters(self):
        self.assertEqual(reverse_template('plain'), reverse('plain'))

    def test_reverse_template__returns_route_parameter_names__when_paramnames_omitted(self):
        self.assertEqual(reverse_template('comment'), '/posts/{post_id}/comments/{comment_id}')

    def test_reverse_template__returns_template__when_parameter_not_after_slash(self):
        self.assertEqual(reverse_template('file'), '/files/file-{file_id}')

    def test_reverse_template__keeps_literal_segment__when_route_contains_slash_one(self):
        self.assertEqual(reverse_template('literal_one'), '/v1/1/{item_id}')

    def test_reverse_template__returns_every_placeholder__when_route_has_eleven_parameters(self):
        expected = '/' + '/'.join('{p' + str(i) + '}' for i in range(11))

        self.assertEqual(reverse_template('eleven'), expected)

    def test_reverse_template__returns_template__when_converters_reject_digits(self):
        self.assertEqual(reverse_template('converters'), '/things/{thing_id}/{thing_slug}/{rest}')

    def test_reverse_template__includes_prefix__when_route_is_included(self):
        self.assertEqual(reverse_template('section_page'), '/section/pages/{page_id}')

    def test_reverse_template__includes_prefix__when_name_is_namespaced(self):
        self.assertEqual(reverse_template('outer:post'), '/outer/posts/{post_id}')

    def test_reverse_template__includes_every_prefix__when_namespaces_are_nested(self):
        self.assertEqual(reverse_template('outer:inner:item'), '/outer/nested/items/{item_id}')

    def test_reverse_template__uses_default_instance__when_name_uses_app_namespace(self):
        self.assertEqual(reverse('outer_app:post', args=[1]), '/app-default/posts/1')
        self.assertEqual(reverse_template('outer_app:post'), '/app-default/posts/{post_id}')

    def test_reverse_template__includes_script_prefix__when_one_is_set(self):
        with override_script_prefix('/mounted/'):
            self.assertEqual(reverse_template('outer:post'), '/mounted/outer/posts/{post_id}')

    def test_reverse_template__renames_placeholders_in_order__when_paramnames_given(self):
        self.assertEqual(
            reverse_template('comment', ['a', 'b']),
            '/posts/{a}/comments/{b}')

    def test_reverse_template__names_unnamed_group__when_paramnames_given(self):
        self.assertEqual(reverse_template('unnamed_group', ['legacy_id']), '/legacy/{legacy_id}/')

    def test_reverse_template__chooses_route_by_parameter_count__when_paramnames_given(self):
        self.assertEqual(reverse_template('optional_group', ['page']), '/optional/{page}/')

    def test_reverse_template__fails__when_routes_for_name_differ_in_parameters(self):
        with self.assertRaises(ValueError):
            reverse_template('optional_group')

    def test_reverse_template__fails__when_paramnames_count_differs_from_route(self):
        with self.assertRaises(NoReverseMatch):
            reverse_template('comment', ['post_id'])

    def test_reverse_template__fails__when_name_is_unknown(self):
        with self.assertRaises(NoReverseMatch):
            reverse_template('missing')

    def test_reverse_template__fails__when_namespace_is_unknown(self):
        with self.assertRaises(NoReverseMatch):
            reverse_template('missing:post')
