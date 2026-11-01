# Node and package managers

The frontend `ww_create_app` writes is built by npm: `npm install` for the npm package
`django-website-widgets` (the framework TypeScript) and the build tools, `npm run build` or
`npm run build:production` for the bundle, and `npm run watch`, which `start_npm_watch()` starts
beside `runserver` (`npm_watch.md`). Read this when Node isn't installed, or when a project uses
yarn, pnpm or another package manager. `ww_doctor` says which is the case
(`checking_the_setup.md`).

**Upgrading the npm package** follows the Python package: after a Python upgrade, `ww_upgrade`
sets the npm package's range in `package.json` to the one the new release works with, and
`npm install` then installs it. To take a newer npm release inside that range without a Python
upgrade, run `npm update django-website-widgets`.

## Installing Node

**Install Node.js, which includes npm: https://nodejs.org.** It's the recommended route, a
one-time step, and what every JavaScript tool and tutorial assumes. Any current LTS release
works; the starter's build tools need at least 18.12.

## Building without Node, in a container

A machine with docker or podman but no Node can run npm in a Node container, with the app's
folder mounted. From the website app's folder (`website/`):

```bash
# docker
docker run --rm --init -it --user "$(id -u):$(id -g)" -v "$PWD":/app:z -w /app \
    -e npm_config_cache=/app/node_modules/.cache/npm \
    docker.io/library/node:24-slim npm install

# podman
podman run --rm --init -it --userns=keep-id -v "$PWD":/app:z -w /app \
    -e npm_config_cache=/app/node_modules/.cache/npm \
    docker.io/library/node:24-slim npm install
```

Swap `npm install` for `npm run build`, or `npm run watch` in a terminal of its own beside
`runserver`, since `start_npm_watch()` runs npm on the machine and finds none. Each option is
there for a reason found the hard way:

- **`--user` (docker) or `--userns=keep-id` (rootless podman):** without it, `node_modules` and
  the built bundle belong to root, and the next edit or install from the machine fails. Leave
  `--user` out on Windows, which has no user ids.
- **`:z` on the mount:** SELinux (Fedora and others) refuses a container a mount not labelled
  for it. Leave it out on macOS and Windows.
- **The image's full name,** `docker.io/library/node:24-slim`: podman refuses a short name like
  `node:24-slim` when it has no alias for it and no terminal to ask which registry. Any Node
  LTS image works.
- **`npm_config_cache` inside `node_modules`:** the user isn't the image's own, so npm's default
  cache directory isn't writable, and inside the mount the cache survives for the next install.
- **`--init`:** Ctrl+C stops npm inside, not just the client.
- **`-it`:** npm's progress and colours in a terminal; leave it out in a script or CI.

**On macOS and Windows, `node_modules` is built for Linux.** A package that ships a native
binary works inside the container but not with npm run on the machine itself. The starter's
build tools are all plain JavaScript (`sass`, not `sass-embedded`), so its build is
unaffected; a project that adds a package with a native binary, and later installs Node,
reinstalls (`npm ci`) before running npm on the machine.

## yarn, pnpm and the rest

The starter's `package.json` works with any of them: `yarn install`, `yarn build`. What's
npm-specific is `start_npm_watch()`, which runs `npm run watch`. A project on another package
manager calls its own watcher from `manage.py` instead, and `website_widgets.npm_watch` is the
model for one: start only for `runserver`, never in the autoreloader's child, and not when a
watcher is already running in the app's folder (`npm_watch.md`).

The package supports npm only for now. Someone who knows another package manager well, and has
a watcher for it proven in their own project, is welcome to open a pull request adding it.
