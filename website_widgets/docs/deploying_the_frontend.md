# Deploying the frontend

A lesson: building the bundle for production, and serving it so a deploy reaches every
visitor's browser instead of their stale cached copy. Read this before a site's first deploy.
How a project hosts Django is its own choice; this covers only what the package's build adds.

## The production build

```bash
# In the website app's folder
npm ci
npm run build:production
```

`npm ci` installs exactly what `package-lock.json` pins, so the build tools a deploy uses are
the ones tested.

`build:production` is the starter's `webpack --node-env production`: minified, and without the
source maps the development build writes. It writes into the website app's `static/`:

- `main.js`, the bundle every page imports from `{% static "main.js" %}`;
- `bundled-styles.css`, every stylesheet `main.ts` imports, which the document template links;
- `chunks/`, the code split off by a dynamic `import()`, such as a charting library only one
  page loads, each file named with its content hash (`chunks/[name].[contenthash].js`).

**The build runs in the deploy, not in git.** The starter's `.gitignore` leaves these files out,
so each deploy builds from its own checkout, in CI or in the image, before `collectstatic`.
Node is only needed to build: once the files exist, Django serves them as static files, so a
deploy image can build in one stage and leave Node out of the one that runs. A deploy machine
without Node can build in a container (`node_and_package_managers.md`).

## Cache busting

Static files are worth caching for a long time, but a browser holding last week's `main.js`
for a year runs last week's code against this week's pages. The fix is a URL that changes
whenever the file does:

```python
STORAGES = {
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage',
    },
    ...
}
```

`collectstatic` then saves a copy of each file under a name with its content hash
(`main.3f2a1c9e.js`), and `{% static %}` writes that name, so a rebuilt file gets a new URL and
an unchanged one keeps its URL and its cache. That only works for URLs made by `static()`:

- **Templates use `{% static %}`,** as the starter's do, never a hand-written `/static/` path.
- **A static file the frontend needs comes through `AppUrls`,** from `static()` in the `AppUrls`
  widget, not written into TypeScript (`starter_site.md`).
- **Chunks are hashed by webpack, not by Django.** The bundle requests them itself, at a URL
  relative to `main.js`, so `static()` never sees them; the hash in their own filename does the
  same job.
