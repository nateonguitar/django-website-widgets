"""
Test case classes and a runner subclass for the runner's tests to build suites from. In a module
whose name doesn't start with `test`, so the package's own test run never discovers them.
"""

import unittest
from unittest.mock import patch

from django.test import tag

from website_widgets.testing import WebsiteWidgetsTestRunner


class ServerTests(unittest.TestCase):
    def test_server__answers(self):
        pass


@tag('playwright')
class BrowserTests(unittest.TestCase):
    def test_browser__clicks(self):
        pass


class OneBrowserTestTests(unittest.TestCase):
    @tag('playwright')
    def test_browser__clicks(self):
        pass

    def test_server__answers(self):
        pass


@unittest.skip('the browser is not installed')
@tag('playwright')
class SkippedBrowserTests(unittest.TestCase):
    def test_browser__clicks(self):
        pass


@tag('browser')
class OtherTagBrowserTests(unittest.TestCase):
    def test_browser__clicks(self):
        pass


class SwitchedOff:
    """What `SwitchingRunner`'s patch replaces: `is_on` is False only while the patch is started."""

    is_on = True


class SwitchingRunner(WebsiteWidgetsTestRunner):
    """A project's subclass, with one patch."""

    @classmethod
    def patches(cls) -> list:
        switch_off = patch.object(SwitchedOff, 'is_on', False)
        return [switch_off]
