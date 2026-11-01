from django.test import SimpleTestCase

from website_widgets.management.npm_package import NpmVersion


class NpmVersionTestCase(SimpleTestCase):
    def test_parse__reads_each_part__when_version_has_a_prerelease(self):
        version = NpmVersion.parse('1.2.3-rc.4')

        self.assertEqual(version.release(), (1, 2, 3))
        self.assertEqual(version.prerelease, ('rc', '4'))
        self.assertEqual(version.as_text(), '1.2.3-rc.4')

    def test_parse__returns_none__when_text_is_not_a_version(self):
        for text in ('latest', '1.2', 'file:../frontend', None):
            with self.subTest(text=text):
                self.assertIsNone(NpmVersion.parse(text))

    def test_is_at_least__orders_by_npm_rules__when_versions_differ(self):
        ascending = ('1.0.0-alpha', '1.0.0-alpha.1', '1.0.0-rc.1', '1.0.0-rc.2', '1.0.0-rc.10', '1.0.0', '1.0.1', '1.1.0')
        for lower, higher in zip(ascending, ascending[1:]):
            with self.subTest(lower=lower, higher=higher):
                self.assertTrue(NpmVersion.parse(higher).is_at_least(NpmVersion.parse(lower)))
                self.assertFalse(NpmVersion.parse(lower).is_at_least(NpmVersion.parse(higher)))
