# packaging

The repository is the engine's home; these are the two registries it is also published to.

- **PyPI** is built by `packaging/pypi/build.py`, not by `uv build` at the root. The engine is
  one file that expects a checkout around it — `CODE = parents[1]`, holding `skills/`, `setup/`
  and `hooks/` — and setuptools cannot ship data files beside a bare module. So the build stages
  a copy: the wheel carries a complete mini-checkout at `humona/_payload/`, with the engine at its
  usual place inside it, and `humona/__init__.py` is a shim that loads it and re-exports `main`
  for the console script. `CODE = parents[1]` then lands on `_payload` with no special case, and
  `setup/install.py` runs there unmodified.

  Both payloads are staged by `packaging/payload.py`, which marks the copy with the registry's
  name in a `PACKAGED` file. The engine reads it for the two things that differ in an installed
  copy, both covered by `TestPackagedInstall`: `humona upgrade` names the registry instead of
  reaching for git, and the vault falls back to `~/humona/vault` rather than to a directory the
  next upgrade replaces. The marker is not a dotfile on purpose — setuptools' `package-data`
  globs skip dot-entries, so a `.packaged` marker would silently not ship and an installed copy
  would think it was a checkout.

  Measured on 2026-10-21: the wheel is 33 files, and in a clean venv `humona doctor` passes
  22/22 after running the bundled `setup/install.py`. Versions `0.0.1` on both registries predate
  this and are only the reserved name.
- **npm/** is built by `packaging/npm/build.py`, not by `npm publish` in that directory: it holds
  the wrapper without the payload. The staged tarball carries the same mini-checkout the wheel
  does, and `bin/humona.js` chooses a Python interpreter (`py -3` first on Windows, `python3`
  elsewhere, `python` last because it is 2.7 on some systems), hands over argv with inherited
  stdio, and passes the exit code back — reporting a signal death the way a shell does. There is
  no postinstall step: nothing is compiled or downloaded, and wiring hooks behind the user's back
  would be the wrong default. The version comes from the engine, so the two registries cannot
  drift apart.

  Measured on 2026-10-21: the tarball is 24 files and 102 KB, and `humona doctor` passes 22/22
  after `npm install -g` and the bundled installer.

Both registries are published by `.github/workflows/release.yml` through trusted publishing:
no tokens are stored anywhere, the registries verify the workflow's OIDC identity instead.
