#!/usr/bin/env python3
"""Build the PyPI wheel from a staging copy, so the checkout's own layout never has to change.

The engine needs a payload beside it and resolves it as `CODE = parents[1]`, the repo root.
A wheel has no repo, and setuptools cannot ship data files next to a bare module. So the wheel
gets a complete mini-checkout at `humona/_payload/`, with the engine at its usual place inside
it, and `humona/__init__.py` is a shim that loads it and re-exports `main` for the console
script. `CODE = parents[1]` then lands on `_payload` with no special case in the engine, and
`setup/install.py` runs there unmodified.

    python3 packaging/pypi/build.py            # build into dist/
    python3 packaging/pypi/build.py -o /tmp/x  # or somewhere else
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import payload  # noqa: E402  (the shared mini-checkout, one directory up)

REPO = payload.REPO

SHIM = '''"""humona — installed from a wheel.

The engine is a single file that expects a checkout around it, so the wheel carries one at
`_payload/`. This module loads the engine from there and re-exports `main` for the console
script, which keeps one copy of the engine in the wheel instead of two.
"""
import importlib.util
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "_payload" / "engine" / "humona.py"
_spec = importlib.util.spec_from_file_location("humona._engine", _SRC)
_engine = importlib.util.module_from_spec(_spec)
sys.modules["humona._engine"] = _engine
_spec.loader.exec_module(_engine)

main = _engine.main
VERSION = _engine.VERSION
'''


def read_metadata():
    """Take [project] from the repo's pyproject verbatim; only the build backend config differs."""
    text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    head, sep, _ = text.partition("[tool.setuptools]")
    if not sep:
        sys.exit("pyproject.toml has no [tool.setuptools] section to replace")
    return head.rstrip() + """

[tool.setuptools]
packages = ["humona"]

[tool.setuptools.package-data]
humona = ["_payload/**/*"]
"""


def stage(root):
    pkg = root / "humona"
    pkg.mkdir(parents=True)
    payload.stage(pkg / "_payload", "pypi")
    (pkg / "__init__.py").write_text(SHIM, encoding="utf-8")
    (root / "pyproject.toml").write_text(read_metadata(), encoding="utf-8")
    shutil.copy2(REPO / "LICENSE", root / "LICENSE")
    shutil.copy2(REPO / "README.md", root / "README.md")
    return root


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", default=str(REPO / "dist"), help="where the wheel lands")
    ap.add_argument("--keep", action="store_true", help="leave the staging tree in place")
    a = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="humona-wheel-"))
    try:
        stage(tmp)
        cmd = ["uv", "build", "--wheel", "--sdist", "-o", str(Path(a.out).resolve())]
        if shutil.which("uv") is None:
            cmd = [sys.executable, "-m", "build", "--wheel", "--sdist",
                   "-o", str(Path(a.out).resolve())]
        r = subprocess.run(cmd, cwd=str(tmp))
        if a.keep:
            print("staging kept at %s" % tmp)
        return r.returncode
    finally:
        if not a.keep:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
