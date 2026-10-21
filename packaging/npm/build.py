#!/usr/bin/env python3
"""Stage the npm package: the same mini-checkout the wheel carries, plus the Node wrapper.

`npx humona` has to reach a Python file, so the tarball ships the payload at `_payload/` and
`bin/humona.js` chooses an interpreter and hands over argv. Nothing is compiled and nothing is
downloaded, so there is no postinstall step.

    python3 packaging/npm/build.py              # stage and `npm pack` into dist/
    python3 packaging/npm/build.py --publish    # ...and publish it
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import payload  # noqa: E402

REPO = payload.REPO
HERE = Path(__file__).resolve().parent


def stage(root):
    shutil.copytree(HERE / "bin", root / "bin")
    shutil.copy2(HERE / "README.md", root / "README.md")
    shutil.copy2(REPO / "LICENSE", root / "LICENSE")

    manifest = json.loads((HERE / "package.json").read_text(encoding="utf-8"))
    manifest["version"] = payload.version()      # one source of truth: the engine
    (root / "package.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    payload.stage(root / "_payload", "npm")
    return root


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", default=str(REPO / "dist"), help="where the tarball lands")
    ap.add_argument("--publish", action="store_true", help="npm publish instead of npm pack")
    ap.add_argument("--keep", action="store_true", help="leave the staging tree in place")
    a = ap.parse_args()

    if shutil.which("npm") is None:
        sys.exit("npm is not on PATH")

    tmp = Path(tempfile.mkdtemp(prefix="humona-npm-"))
    try:
        stage(tmp)
        out = Path(a.out).resolve()
        out.mkdir(parents=True, exist_ok=True)
        if a.publish:
            cmd = ["npm", "publish", "--access", "public"]
            # Provenance is signed from the workflow's OIDC identity, so it only works in CI.
            if os.environ.get("GITHUB_ACTIONS") == "true":
                cmd.append("--provenance")
        else:
            cmd = ["npm", "pack", "--pack-destination", str(out)]
        r = subprocess.run(cmd, cwd=str(tmp))
        if a.keep:
            print("staging kept at %s" % tmp)
        return r.returncode
    finally:
        if not a.keep:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
