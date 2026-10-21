# packaging

The repository is the engine's home; these are the two registries it is also published to.

- **PyPI** is built by `packaging/pypi/build.py`, not by `uv build` at the root. The engine is
  one file that expects a checkout around it — `CODE = parents[1]`, holding `skills/`, `setup/`
  and `hooks/` — and setuptools cannot ship data files beside a bare module. So the build stages
  a copy: the wheel carries a complete mini-checkout at `humona/_payload/`, with the engine at its
  usual place inside it, and `humona/__init__.py` is a shim that loads it and re-exports `main`
  for the console script. `CODE = parents[1]` then lands on `_payload` with no special case, and
  `setup/install.py` runs there unmodified.

  Two things the payload is marked with, both covered by `TestWheelInstall`: `PYPI_WHEEL` tells
  the engine it cannot upgrade itself with git (`humona upgrade` prints `pip install -U humona`),
  and it keeps the vault out of `site-packages`, which `pip install -U` replaces. The marker is
  not a dotfile on purpose: setuptools' `package-data` globs skip dot-entries, so a `.wheel`
  marker would silently not ship.

  Measured on 2026-10-21: the wheel is 33 files, and in a clean venv `humona doctor` passes
  22/22 after running the bundled `setup/install.py`. Version `0.0.1` on PyPI predates this and
  is only the reserved name — it still points at the repo, so `pip install humona` is not worth
  documenting in the README until 3.0.0 is published.
- **npm/** is a wrapper package. Today it prints the same pointer; the engine is Python and
  `npx humona` cannot usefully pretend otherwise until the packaged release lands. Its version
  is deliberately independent of the engine's — it is a pointer, not the engine.

Both registries are published by `.github/workflows/release.yml` through trusted publishing:
no tokens are stored anywhere, the registries verify the workflow's OIDC identity instead.
