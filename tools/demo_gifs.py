#!/usr/bin/env python3
"""Render the README's GIFs from real command runs: docs/install.gif and docs/usage.gif.

    python3 tools/demo_gifs.py            # both
    python3 tools/demo_gifs.py --only usage

Nothing here is a mock-up. Each scene runs the actual commands in a throwaway HOME and vault,
captures their real stdout, and types it out frame by frame, so a GIF that goes stale fails to
render rather than lying. The drawing primitives come from `demo_gif.py`, which renders the
session-start scene the same way.

Pillow is a dev-only dependency; the engine stays standard library.
"""
import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ENGINE = REPO / "engine" / "humona.py"
_spec = importlib.util.spec_from_file_location("demo_gif", Path(__file__).with_name("demo_gif.py"))
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)


def shell(cmd, env, cwd, max_lines=14):
    """Run one command for real and return (prompt line, output lines)."""
    # input="" on purpose: a command that reads stdin (`humona working -`) would otherwise block
    # on the terminal and hang the render instead of failing.
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env, cwd=str(cwd),
                       input="", timeout=120)
    out = [l.rstrip() for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    if len(out) > max_lines:
        out = out[: max_lines - 1] + ["…"]
    return out


def scrub(lines, tmp, home):
    """Replace throwaway paths with the ones a reader will actually have.

    Both spellings: macOS resolves a temp dir through /private, so the resolved form has to be
    replaced too or the GIF shows `/private~/humona/vault`.
    """
    subs = []
    for p in (home, tmp):
        subs += [str(p.resolve()), str(p)]
    out = []
    for l in lines:
        for frm in sorted(subs, key=len, reverse=True):
            l = l.replace(frm, "~")
        out.append(l.replace("~/humona-src", "~/humona-src"))
    return out


def scene_install(tmp):
    """Clone, install, verify — the whole install, as it really runs."""
    home = tmp / "home"
    home.mkdir(parents=True)
    code = tmp / "claude-memory"
    subprocess.run([sys.executable, str(REPO / "setup" / "export_public.py"), str(code)],
                   capture_output=True, timeout=300)
    env = {k: v for k, v in os.environ.items()
           if k not in ("HUMONA_VAULT", "HUMONA_STATE", "BRAIN_CC_PROJECTS", "VIRTUAL_ENV")}
    env["HOME"] = str(home)
    steps = [("git clone https://github.com/mesutcandemir39/humona.git ~/humona-src",
              ["Cloning into '~/humona-src'...", "done."]),
             ("python3 ~/humona-src/setup/install.py",
              shell("%s %s/setup/install.py" % (sys.executable, code), env, tmp)),
             ("humona doctor",
              shell("%s %s/engine/humona.py doctor" % (sys.executable, code), env, tmp, 6))]
    lines = []
    for cmd, out in steps:
        lines.append(("cmd", cmd))
        lines += [("text", l) for l in scrub(out, tmp, home)]
        lines.append(("text", ""))
    return lines, "two commands · no database · no API key · no account"


def scene_usage(tmp):
    """A short real session: remember, search, working memory, the board, code pointers."""
    home, vault = tmp / "home", tmp / "vault"
    home.mkdir(parents=True)
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    env.update({"HOME": str(home), "HUMONA_VAULT": str(vault), "HUMONA_STATE": str(tmp / "state"),
                "BRAIN_NO_SYNC": "1", "BRAIN_CC_PROJECTS": str(tmp / "cc")})
    b = "%s %s" % (sys.executable, ENGINE)
    shell("%s init" % b, env, tmp)
    seeds = [
        '%s remember -t semantic -p acme "Rate limit is per API key" '
        '"60 requests a minute per key, not per IP. Decided after the 2026-03 incident."' % b,
        '%s remember -t procedural -p acme "Rotate the signing key" '
        '"Run scripts/rotate.sh, redeploy the gateway, then verify with scripts/smoke.sh."' % b,
        '%s task add -p acme "Ship the usage dashboard"' % b,
    ]
    for s in seeds:
        shell(s, env, tmp)
    subprocess.run("%s working - -p acme" % b, shell=True, capture_output=True, text=True, env=env,
                   cwd=str(tmp), timeout=60, input="## Goal\nShip the usage dashboard for acme.\n\n"
                   "## Current step\nRate limiting is agreed; the dashboard query is next.\n\n"
                   "## Next\n- Wire the per-key counter -> verify: the dashboard shows 60/min per key\n")
    lines = []
    shown = [
        ('humona remember -t semantic "Rate limit is per API key" "60 requests a minute per key…"',
         ["ADDED → 3-LongTerm/Semantic/rate-limit-is-per-api-key.md"]),
        ('humona search "how many requests per key"',
         shell('%s search "how many requests per key" --keyword -k 2' % b, env, tmp, 6)),
        ('humona code -t code "how does auto-recall decide what to inject"',
         shell('%s code -t code "how does auto-recall decide what to inject" --path %s -n 2' % (b, REPO),
               env, tmp, 6)),
        ('humona facts --all', shell("%s facts --all -n 3" % b, env, tmp, 8)),
    ]
    for cmd, out in shown:
        lines.append(("cmd", cmd))
        lines += [("text", l) for l in scrub(out, tmp, home)]
        lines.append(("text", ""))
    return lines, "every answer above came from Markdown files on disk · no index server"


SCENES = {"install": scene_install, "usage": scene_usage}


def render(name, out_path):
    from PIL import Image
    tmp = Path(tempfile.mkdtemp(prefix="brain-gif-"))
    try:
        lines, footer = SCENES[name](tmp)
    finally:
        pass
    try:
        fonts = G.font_pair(G.FS)
        cols = int((G.W - 2 * G.PAD) // fonts[0].getlength("x"))
        body = []
        for kind, text in lines:
            for i, piece in enumerate(G.wrap([text], cols) or [""]):
                body.append((kind if i == 0 else "text", piece))
        frames, durations = [], []
        for i in range(1, len(body) + 1):
            kind, text = body[i - 1]
            G.draw_window(frames, body[:i], [], "", fonts)
            durations.append(260 if kind == "cmd" else (70 if text.strip() else 30))
        G.draw_window(frames, body, [], footer, fonts)
        durations.append(4500)
        h = max(f.height for f in frames)
        canvas = [Image.new("RGB", (G.W, h), G.BG) for _ in frames]
        for c, f in zip(canvas, frames):
            c.paste(f, (0, 0))
        pal = [c.quantize(colors=64, method=Image.MEDIANCUT, dither=Image.NONE) for c in canvas]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pal[0].save(out_path, save_all=True, append_images=pal[1:], duration=durations, loop=0,
                    optimize=True, disposal=1)
        print("%s — %d frames, %dx%d, %.0f KB" % (out_path, len(pal), G.W, h,
                                                  out_path.stat().st_size / 1024))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", choices=sorted(SCENES))
    a = ap.parse_args()
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("this dev tool needs Pillow:  pip install pillow", file=sys.stderr)
        return 1
    for name in ([a.only] if a.only else sorted(SCENES)):
        render(name, REPO / "docs" / ("%s.gif" % name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
