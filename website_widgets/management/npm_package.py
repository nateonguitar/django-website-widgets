import json
import os
import re
from dataclasses import dataclass

from django.apps import apps
from django.core import checks

from website_widgets.config import get_config


@dataclass(frozen=True)
class NpmVersion:
    """A semantic version as npm writes it, `1.0.0` or `1.0.0-rc.1`, compared by npm's rules."""

    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...]

    VERSION_RE = re.compile(r'^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$')

    @classmethod
    def parse(cls, text: str) -> 'NpmVersion | None':
        match = cls.VERSION_RE.match(text.strip()) if isinstance(text, str) else None
        if match is None:
            return None
        major, minor, patch, prerelease = match.groups()
        return cls(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            prerelease=tuple(prerelease.split('.')) if prerelease else ())

    def release(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def as_text(self) -> str:
        text = f'{self.major}.{self.minor}.{self.patch}'
        return f'{text}-{".".join(self.prerelease)}' if self.prerelease else text

    def is_at_least(self, other: 'NpmVersion') -> bool:
        return self._sort_key() >= other._sort_key()

    def _sort_key(self) -> tuple:
        # A release ranks above its own prereleases, and a numeric identifier below a word.
        identifiers = tuple(
            (0, int(identifier), '') if identifier.isdigit() else (1, 0, identifier)
            for identifier in self.prerelease
        )
        is_release = 0 if self.prerelease else 1
        return (*self.release(), is_release, identifiers)


class NpmPackage:
    """
    The npm package, `django-website-widgets` on npm, which holds the TypeScript a project's
    controllers import. It is versioned apart from this Python package, which declares the range
    of it that it works with: `ww_create_app` writes the range into a new app's `package.json`,
    `ww_upgrade` sets it there, and a system check and `ww_doctor` compare it with what is
    installed.
    """

    NAME = 'django-website-widgets'
    # The npm releases this Python release works with, a caret range. Raised when the Python side
    # starts relying on something only a newer npm release has, after that release is published.
    RANGE = '^1.0.0-rc.1'

    @classmethod
    def range_minimum(cls) -> NpmVersion:
        return NpmVersion.parse(cls.RANGE.removeprefix('^'))

    @classmethod
    def range_allows(cls, version: NpmVersion) -> bool:
        """Whether `version` is in `RANGE`, by npm's rules for a caret range."""
        minimum = cls.range_minimum()
        if version.major != minimum.major or not version.is_at_least(minimum):
            return False
        # npm lets a prerelease through only for the release the range itself names.
        return not version.prerelease or version.release() == minimum.release()

    @classmethod
    def declared_spec(cls, package_json: dict) -> str | None:
        """What `package.json` asks for, from `dependencies` or `devDependencies`, or `None`."""
        for section_name in ('dependencies', 'devDependencies'):
            section = package_json.get(section_name)
            if isinstance(section, dict) and isinstance(section.get(cls.NAME), str):
                return section[cls.NAME]
        return None

    @staticmethod
    def is_registry_spec(spec: str) -> bool:
        """
        Whether a spec names versions from the npm registry. One that names a folder, git or an
        alias (`file:../../../frontend`, `github:…`, `npm:…`) is the developer's choice, left alone.
        """
        return ':' not in spec and not spec.startswith(('.', '/', '~/'))

    @classmethod
    def installed_version(cls, app_folder: str) -> NpmVersion | None:
        """The version in the app's `node_modules/`, or `None` when it isn't installed."""
        path = os.path.join(app_folder, 'node_modules', cls.NAME, 'package.json')
        if not os.path.isfile(path):
            return None
        try:
            with open(path, encoding='utf-8') as file:
                package_json = json.load(file)
        except ValueError:
            return None
        return NpmVersion.parse(package_json.get('version')) if isinstance(package_json, dict) else None

    @classmethod
    def install_command(cls) -> str:
        return f'npm install {cls.NAME}@"{cls.RANGE}"'

    @staticmethod
    def check_installed_version(app_configs=None, **kwargs) -> list[checks.Warning]:
        """
        A system check: warns when the app's installed npm package is outside the range this
        Python release works with, as after upgrading one half and not the other. Silent without
        the app or its `node_modules/`, since a site may use only the Python half.
        """
        try:
            app_folder = apps.get_app_config(get_config().website_app_name).path
        except LookupError:
            return []
        installed = NpmPackage.installed_version(app_folder)
        if installed is None or NpmPackage.range_allows(installed):
            return []
        return [checks.Warning(
            f'The npm package {NpmPackage.NAME} {installed.as_text()} is installed, but this release of '
            f'the Python package works with {NpmPackage.RANGE}.',
            hint=f'In the website app, run: {NpmPackage.install_command()}',
            id='website_widgets.W002')]
