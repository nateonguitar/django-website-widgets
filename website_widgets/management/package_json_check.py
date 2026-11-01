import json
import os
import re
from dataclasses import dataclass, field

from website_widgets.management.npm_package import NpmPackage, NpmVersion
from website_widgets.management.starter_site import StarterSite


@dataclass(frozen=True)
class PackageJsonFixes:
    """What a website app's `package.json` lacks against the starter site's, and how to fix it."""

    # Set when there is no file to check, or it isn't JSON; nothing else is checked then.
    error: str | None = None
    # `name@^x.y.z` for each build tool missing or declared below the starter's minimum.
    packages_to_install: list[str] = field(default_factory=list)
    # The starter's command for each script it needs and the file lacks.
    missing_scripts: dict[str, str] = field(default_factory=dict)
    # Set when the npm package is missing, or asked for below the range the Python package works with.
    npm_package_out_of_range: bool = False

    def is_empty(self) -> bool:
        return (
            self.error is None
            and not self.packages_to_install
            and not self.missing_scripts
            and not self.npm_package_out_of_range)

    def fix_lines(self, shown_folder: str) -> list[str]:
        """One line per fix, each something to run or add by hand."""
        if self.error is not None:
            return [self.error]
        lines = []
        if self.npm_package_out_of_range:
            lines.append(f'In {shown_folder}/, run: {NpmPackage.install_command()}')
        if self.packages_to_install:
            packages = ' '.join(self.packages_to_install)
            lines.append(f'In {shown_folder}/, run: npm install --save-dev {packages}')
        for name, command in self.missing_scripts.items():
            lines.append(f'Add to "scripts" in {shown_folder}/package.json: "{name}": "{command}"')
        return lines


class PackageJsonCheck:
    """
    Checks a website app's `package.json` against the starter site's: the npm package at the range
    the Python package works with, every build tool the starter lists, declared with at least the
    starter's minimum version, and the scripts `start_npm_watch()` and a build run. It edits
    nothing; `ww_upgrade` sets the npm package's range itself (`BuildFiles`), and prints the rest
    as fixes, as `ww_doctor` does.
    """

    REQUIRED_SCRIPTS = ('build', 'watch')
    # The minimum a declared range allows: `^5.110.2`, `~9.5`, `>=7`, `16.0.4`. Anything else,
    # such as `latest` or a git URL, can't be compared and is accepted.
    MINIMUM_VERSION_RE = re.compile(r'^\s*(?:\^|~|>=|=)?\s*v?(\d+)(?:\.(\d+))?(?:\.(\d+))?')

    def __init__(
        self,
        app_folder: str,
        app_label: str
    ):
        self.path = os.path.join(app_folder, StarterSite.PACKAGE_JSON)
        self.starter = json.loads(StarterSite(app_label).file(StarterSite.PACKAGE_JSON))

    def run(self) -> PackageJsonFixes:
        if not os.path.isfile(self.path):
            return PackageJsonFixes(error=f'There is no {StarterSite.PACKAGE_JSON}.')
        try:
            with open(self.path, encoding='utf-8') as file:
                package_json = json.load(file)
        except ValueError as error:
            return PackageJsonFixes(error=f'{StarterSite.PACKAGE_JSON} is not valid JSON: {error}')
        if not isinstance(package_json, dict):
            return PackageJsonFixes(error=f'{StarterSite.PACKAGE_JSON} holds no JSON object.')

        declared = {
            **self._section(package_json, 'dependencies'),
            **self._section(package_json, 'devDependencies'),
        }
        packages_to_install = []
        for name, starter_range in self.starter['devDependencies'].items():
            starter_minimum = self.minimum_version(starter_range)
            declared_minimum = self.minimum_version(declared[name]) if name in declared else None
            is_missing = name not in declared
            is_too_low = declared_minimum is not None and declared_minimum < starter_minimum
            if is_missing or is_too_low:
                packages_to_install.append(f'{name}@{starter_range}')

        scripts = self._section(package_json, 'scripts')
        missing_scripts = {
            name: self.starter['scripts'][name]
            for name in self.REQUIRED_SCRIPTS
            if name not in scripts
        }
        return PackageJsonFixes(
            packages_to_install=packages_to_install,
            missing_scripts=missing_scripts,
            npm_package_out_of_range=self._npm_package_out_of_range(package_json))

    def _npm_package_out_of_range(self, package_json: dict) -> bool:
        """
        Whether the npm package is missing, or asked for below the range the Python package works
        with. A spec naming a folder or git, as the examples' `file:` one does, is the
        developer's choice and passes.
        """
        spec = NpmPackage.declared_spec(package_json)
        if spec is None:
            return True
        if not NpmPackage.is_registry_spec(spec):
            return False
        declared_minimum = NpmVersion.parse(spec.lstrip('^~=v> '))
        return declared_minimum is not None and not declared_minimum.is_at_least(NpmPackage.range_minimum())

    @classmethod
    def minimum_version(cls, version_range: str) -> tuple[int, int, int] | None:
        """`(5, 110, 2)` for `^5.110.2`, or `None` for a range this can't read."""
        if not isinstance(version_range, str):
            return None
        match = cls.MINIMUM_VERSION_RE.match(version_range)
        if match is None:
            return None
        major, minor, patch = match.groups()
        return (int(major), int(minor or 0), int(patch or 0))

    @staticmethod
    def _section(
        package_json: dict,
        key: str
    ) -> dict:
        """A section such as `devDependencies`, or empty when it's missing or not an object, as `"scripts": null`."""
        section = package_json.get(key)
        return section if isinstance(section, dict) else {}
