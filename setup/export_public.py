#!/usr/bin/env python3
"""Copy this repo into a target directory without any memory — ready to publish.

    python3 setup/export_public.py ~/code/claude-brain-public

Takes the engine, setup, skills, tests, docs and CI; leaves out `memory/`, `private/`,
local state and git history. The result installs with the same `setup/install.py`.
"""
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INCLUDE = ["engine", "setup", "skills", "tests", "tools", "docs",
           # the plugin surface: manifest + marketplace catalogue, hooks, MCP server, bin/ on PATH
           ".claude-plugin", "hooks", "bin", ".mcp.json",
           "README.md", "CHANGELOG.md", "CONTRIBUTING.md", "CLAUDE.md", "AGENTS.md", "ROADMAP.md",
           "SECURITY.md", "VERSIONING.md", "LICENSE", "release.json", "pyproject.toml",
           ".gitattributes", ".gitignore"]
PUBLIC_NAME = "humona"   # the private vault stays `claude-brain`; the published code is this
# CI lives only in the published copy: a private vault burns Actions minutes on every push,
# while a public repo runs them for free. The template is kept in setup/.
WORKFLOW = ("setup/workflow-test.yml", ".github/workflows/test.yml")
# Issue/PR templates live under setup/ in the private vault and become .github/ in the public copy,
# for the same reason as the workflow: GitHub would otherwise act on them in the private repo too.
GITHUB_DIR = ("setup/github", ".github")
MEMORY_DIRS = ["1-ShortTerm", "2-Working", "3-LongTerm/Core", "3-LongTerm/Semantic",
               "3-LongTerm/Episodic", "3-LongTerm/Procedural", "projects", "knowledge", "Archive"]


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip())
        return 2
    dst = Path(sys.argv[1]).expanduser().resolve()
    if dst.exists() and any(dst.iterdir()):
        print("refusing to write into a non-empty directory:", dst)
        return 1
    for name in INCLUDE:
        src = REPO / name
        if not src.exists():
            continue
        if src.is_dir():
            shutil.copytree(src, dst / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst / name)
    src, out = REPO / GITHUB_DIR[0], dst / GITHUB_DIR[1]
    if src.exists():
        shutil.copytree(src, out, dirs_exist_ok=True)
        shutil.rmtree(dst / GITHUB_DIR[0], ignore_errors=True)   # not needed twice
    src, out = REPO / WORKFLOW[0], dst / WORKFLOW[1]
    if src.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
        (dst / WORKFLOW[0]).unlink(missing_ok=True)  # the template is not needed twice
    for d in MEMORY_DIRS:  # empty layers, so a fresh clone has somewhere to write
        (dst / "memory" / d).mkdir(parents=True, exist_ok=True)
        (dst / "memory" / d / ".gitkeep").touch()
    print("public copy written to", dst)
    print("next:\n  cd %s\n  git init && git add -A && git commit -m \"%s %s\"\n"
          "  gh repo create %s --public --source . --push\n  python3 tests/test_humona.py"
          % (dst, PUBLIC_NAME, (REPO / "pyproject.toml").exists() and "release" or "", PUBLIC_NAME))
    return 0


if __name__ == "__main__":
    sys.exit(main())
