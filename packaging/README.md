# packaging

The repository is the engine's home; these are the two registries it is also published to.

- **PyPI** is built from the root `pyproject.toml`. It is **not releasable yet**: the wheel
  carries `humona.py` and nothing else, so an installed copy has no hooks, no skills and no
  installer, and `humona doctor` fails 13 of its checks. Version `0.0.1` on PyPI is the name,
  registered early, with a module that prints where the real install lives.
- **npm/** is a wrapper package. Today it prints the same pointer; the engine is Python and
  `npx humona` cannot usefully pretend otherwise until the packaged release lands. Its version
  is deliberately independent of the engine's — it is a pointer, not the engine.

Both registries are published by `.github/workflows/release.yml` through trusted publishing:
no tokens are stored anywhere, the registries verify the workflow's OIDC identity instead.
