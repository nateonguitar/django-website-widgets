import os


PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class StarterSite:
    """
    The working site `ww_create_app` writes into a new website app: every file under the
    package's `starter_site/`, at the same path, with `.tmpl` dropped and the placeholders filled
    in. From then on the files are the developer's. `ww_upgrade` reads only the build files
    (`BUILD_CONFIGS` and `PACKAGE_JSON`) from here, to compare a project's against.
    """

    TEMPLATES_DIR = os.path.join(PACKAGE_DIR, 'starter_site')
    # Compared with the project's on every `ww_upgrade`, which offers to replace one that differs.
    BUILD_CONFIGS = ('webpack.config.js', 'tsconfig.json')
    # Created when missing, otherwise only checked; see `PackageJsonCheck`.
    PACKAGE_JSON = 'package.json'

    def __init__(self, app_label: str):
        self.app_label = app_label

    def files(self) -> dict[str, str]:
        """Every file, by its path in the app with `/` separators, filled in for this app."""
        files = {}
        for folder, subfolders, filenames in os.walk(self.TEMPLATES_DIR):
            subfolders[:] = sorted(subfolder for subfolder in subfolders if subfolder != '__pycache__')
            for filename in sorted(filenames):
                if not filename.endswith('.tmpl'):
                    continue
                template_path = os.path.join(folder, filename)
                path = os.path \
                    .relpath(template_path, self.TEMPLATES_DIR) \
                    .removesuffix('.tmpl') \
                    .replace(os.sep, '/')
                files[path] = self._fill(template_path)
        return files

    def file(self, path: str) -> str:
        """One file, by its path in the app, filled in for this app."""
        return self._fill(os.path.join(self.TEMPLATES_DIR, f'{path}.tmpl'))

    def _fill(self, template_path: str) -> str:
        with open(template_path, encoding='utf-8') as file:
            content = file.read()
        config_class_name = ''.join(part.title() for part in self.app_label.split('_')) + 'Config'
        # npm package names are lowercase, with no underscores by convention.
        npm_package_name = self.app_label.lower().replace('_', '-')
        return content \
            .replace('__app_label__', self.app_label) \
            .replace('__AppConfigClass__', config_class_name) \
            .replace('__npm_package_name__', npm_package_name)
