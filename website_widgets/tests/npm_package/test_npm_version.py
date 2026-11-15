from django.test import SimpleTestCase

from website_widgets.management.npm_package import NpmVersion


class NpmVersionTestCase(SimpleTestCase):
    def test_parse__reads_each_part__when_version_has_a_prerelease(self):
        version = NpmVersion.parse('1.2.3-rc.4')

        release = version.release()
        text = version.as_text()
        self.assertEqual(release, (1, 2, 3))
        self.assertEqual(version.prerelease, ('rc', '4'))
        self.assertEqual(text, '1.2.3-rc.4')

    def test_parse__returns_none__when_text_is_not_a_version(self):
        for text in ('latest', '1.2', 'file:../frontend', None):
            with self.subTest(text=text):
                version = NpmVersion.parse(text)

                self.assertIsNone(version)

    def test_is_at_least__orders_by_npm_rules__when_versions_differ(self):
        ascending = ('1.0.0-alpha', '1.0.0-alpha.1', '1.0.0-rc.1', '1.0.0-rc.2', '1.0.0-rc.10', '1.0.0', '1.0.1', '1.1.0')
        for lower_text, higher_text in zip(ascending, ascending[1:]):
            with self.subTest(lower=lower_text, higher=higher_text):
                lower = NpmVersion.parse(lower_text)
                higher = NpmVersion.parse(higher_text)

                higher_is_at_least_lower = higher.is_at_least(lower)
                lower_is_at_least_higher = lower.is_at_least(higher)

                self.assertTrue(higher_is_at_least_lower)
                self.assertFalse(lower_is_at_least_higher)
