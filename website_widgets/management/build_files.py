import difflib
import importlib.metadata
import json
import os
import re

from django.core.management.base import OutputWrapper

from website_widgets.management.framework_folder import FrameworkFolder
from website_widgets.management.npm_package import NpmPackage
from website_widgets.management.package_json_check import PackageJsonCheck
from website_widgets.management.starter_site import StarterSite


class BuildFiles:
    """
    A website app's build files, as `ww_upgrade` keeps them against the starter site's. A missing
    one is created, since a build needs it. `webpack.config.js` and `tsconfig.json` are the
    developer's to tune, so one that differs is only replaced on a yes. `package.json` holds the
    developer's own dependencies too, so the only thing written there is the npm package's range,
    the one the installed Python package works with; what else it lacks is printed as fixes.
    """

    def __init__(
        self,
        app_folder: str,
        app_label: str,
        stdout: OutputWrapper,
        interactive: bool
    ):
        self.app_folder = app_folder
        self.app_label = app_label
        self.starter_site = StarterSite(app_label)
        self.stdout = stdout
        self.interactive = interactive
        self.version = importlib.metadata.version('django-website-widgets')

    def update(self):
        for path in StarterSite.BUILD_CONFIGS:
            self._update_config(path)
        self._update_package_json()

    def _update_config(self, path: str):
        starter_content = self.starter_site.file(path)
        file_path = os.path.join(self.app_folder, path)
        shown_path = FrameworkFolder.display_path(file_path)
        if not os.path.isfile(file_path):
            self._write(file_path, starter_content)
            self.stdout.write(f"Created {shown_path} from the starter site's.")
            return
        with open(file_path, encoding='utf-8') as file:
            content = file.read()
        if content == starter_content:
            return
        if not self.interactive:
            self.stdout.write(
                f"Kept {shown_path}, which differs from the starter site's in "
                f"django-website-widgets {self.version}. Rerun without --noinput to compare them.")
            return
        if self._ask_to_replace(shown_path, content, starter_content):
            self._write(file_path, starter_content)
            self.stdout.write(f"Replaced {shown_path} with the starter site's.")
        else:
            self.stdout.write(f'Kept {shown_path}.')

    def _ask_to_replace(
        self,
        shown_path: str,
        content: str,
        starter_content: str
    ) -> bool:
        question = (
            f"{shown_path} differs from the starter site's in django-website-widgets "
            f"{self.version}. Replace it? [y/N, or d to see the difference] ")
        while True:
            answer = FrameworkFolder.read_answer(question)
            if answer not in ('d', 'diff'):
                return answer in ('y', 'yes')
            diff_lines = difflib.unified_diff(
                content.splitlines(keepends=True),
                starter_content.splitlines(keepends=True),
                fromfile=f'{shown_path} (yours)',
                tofile=f"{shown_path} (the starter site's)")
            self.stdout.write(''.join(diff_lines), ending='')
            question = f'Replace {shown_path}? [y/N] '

    def _update_package_json(self):
        file_path = os.path.join(self.app_folder, StarterSite.PACKAGE_JSON)
        shown_folder = FrameworkFolder.display_path(self.app_folder)
        if not os.path.isfile(file_path):
            self._write(file_path, self.starter_site.file(StarterSite.PACKAGE_JSON))
            self.stdout.write(f"Created {shown_folder}/{StarterSite.PACKAGE_JSON} from the starter site's.")
            return
        self._set_npm_package_range(file_path, shown_folder)
        package_json_check = PackageJsonCheck(
            app_folder=self.app_folder,
            app_label=self.app_label)
        fixes = package_json_check.run()
        if fixes.is_empty():
            return
        self.stdout.write(
            f"{shown_folder}/{StarterSite.PACKAGE_JSON} lacks what the starter site's build needs "
            f"in django-website-widgets {self.version}. It is yours, so it wasn't changed:")
        for line in fixes.fix_lines(shown_folder):
            self.stdout.write(f'  {line}')

    def _set_npm_package_range(
        self,
        file_path: str,
        shown_folder: str
    ):
        """
        Sets the npm package to `NpmPackage.RANGE`, in the section that already names it, or in
        `dependencies` when none does. A spec naming a folder or git is left alone. Only that one
        value changes, so the rest of the file keeps its formatting; adding the key rewrites it
        as two-space JSON. Unreadable JSON is left for `PackageJsonCheck` to report.
        """
        with open(file_path, encoding='utf-8') as file:
            content = file.read()
        try:
            package_json = json.loads(content)
        except ValueError:
            return
        if not isinstance(package_json, dict):
            return
        spec = NpmPackage.declared_spec(package_json)
        if spec == NpmPackage.RANGE or (spec is not None and not NpmPackage.is_registry_spec(spec)):
            return
        if spec is None:
            dependencies = package_json.get('dependencies')
            if not isinstance(dependencies, dict):
                dependencies = {}
                package_json['dependencies'] = dependencies
            dependencies[NpmPackage.NAME] = NpmPackage.RANGE
            updated = json.dumps(package_json, indent=2) + '\n'
        else:
            declared = re.compile(rf'("{re.escape(NpmPackage.NAME)}"\s*:\s*)"{re.escape(spec)}"')
            updated = declared.sub(lambda match: f'{match.group(1)}"{NpmPackage.RANGE}"', content, count=1)
        self._write(file_path, updated)
        self.stdout.write(
            f'Set {NpmPackage.NAME} to "{NpmPackage.RANGE}" in {shown_folder}/{StarterSite.PACKAGE_JSON}, '
            f'the range django-website-widgets {self.version} works with. In {shown_folder}/, run: '
            f'npm install')

    @staticmethod
    def _write(
        file_path: str,
        content: str
    ):
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
