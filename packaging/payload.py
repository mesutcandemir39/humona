"""The mini-checkout both registry packages carry, in one place.

`engine/humona.py` resolves everything it needs as `CODE = parents[1]`: a checkout holding
`skills/`, `setup/` and `hooks/`. Neither a wheel nor an npm tarball is a checkout, so each one
ships a trimmed copy of it and marks the copy with the registry's name. The engine reads that
marker to know it cannot upgrade itself with git, and to keep the vault out of a directory that
the next upgrade replaces.
"""
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# What an installed copy needs to work. `tests/` and `tools/` are developer-only, `memory/` is the
# user's own vault and must never ship, and `docs/` is 2.9 MB of GIFs a package has no use for.
DIRS = ["engine", "setup", "skills", "hooks", "bin"]
FILES = ["AGENTS.md", "LICENSE", "README.md", "CHANGELOG.md"]

IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".venv", ".DS_Store")


def stage(dest, registry):
    """Copy the payload into `dest` and mark it as installed from `registry`."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for name in DIRS:
        src = REPO / name
        if not src.is_dir():
            sys.exit("missing payload directory: %s" % name)
        shutil.copytree(src, dest / name, ignore=IGNORE)
    for name in FILES:
        src = REPO / name
        if not src.is_file():
            sys.exit("missing payload file: %s" % name)
        shutil.copy2(src, dest / name)
    (dest / "PACKAGED").write_text(registry + "\n", encoding="utf-8")
    return dest


def version():
    """The engine's version, which every manifest must agree with."""
    for line in (REPO / "engine" / "humona.py").read_text(encoding="utf-8").splitlines():
        if line.startswith("VERSION = "):
            return line.split('"')[1]
    sys.exit("could not read VERSION from engine/humona.py")
