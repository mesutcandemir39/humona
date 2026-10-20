#!/usr/bin/env python3
"""Render docs/session-start.gif: what a session start actually injects.

    python3 tools/demo_gif.py [-o docs/session-start.gif]

The payload in the GIF is not mocked up. The script builds a throwaway vault for a fictional
project (so no real memory is ever published), seeds it through the normal CLI, then runs the
real SessionStart hook and types its output out frame by frame. The footer numbers — characters,
token estimate, hook duration — are measured on that run.

Pillow is needed for the drawing and is a dev-only dependency: the engine itself stays stdlib.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ENGINE = REPO / "engine" / "humona.py"

W, PAD, LH, FS = 940, 18, 22, 15
BG, CHROME, LINE = "#0f1115", "#1b1f27", "#272c36"
C = {"text": "#d7dae0", "tag": "#7aa2f7", "title": "#c0caf5", "dim": "#4e5668",
     "amber": "#e0af68", "green": "#9ece6a", "pink": "#f7768e", "prompt": "#9ece6a"}
FONTS = [("/System/Library/Fonts/Menlo.ttc", 0, 1), ("/System/Library/Fonts/Monaco.ttf", None, None),
         ("/Library/Fonts/Andale Mono.ttf", None, None), ("DejaVuSansMono.ttf", None, None)]


def font_pair(size):
    from PIL import ImageFont
    for path, reg, bold in FONTS:
        try:
            if reg is None:
                f = ImageFont.truetype(path, size)
                return f, f
            return (ImageFont.truetype(path, size, index=reg),
                    ImageFont.truetype(path, size, index=bold))
        except OSError:
            continue
    f = ImageFont.load_default()
    return f, f


# ---------- the fictional vault ----------
def run(args, cwd, env, stdin=""):
    return subprocess.run([sys.executable, str(ENGINE)] + [str(a) for a in args], input=stdin,
                          capture_output=True, text=True, env=env, cwd=str(cwd), timeout=120).stdout


def seed(tmp):
    """A small but realistic vault: two long-term notes, a card, working memory, tasks, episodes."""
    env = dict(os.environ, HUMONA_VAULT=str(tmp / "vault"), HUMONA_STATE=str(tmp / "state"),
               BRAIN_CC_PROJECTS=str(tmp / "cc"), BRAIN_NO_SYNC="1")
    env.pop("VIRTUAL_ENV", None)
    proj = tmp / "projects" / "work" / "acme-dashboard"
    proj.mkdir(parents=True)
    for g in (["init", "-q"], ["remote", "add", "origin", "https://github.com/acme/acme-dashboard.git"]):
        subprocess.run(["git"] + g, cwd=str(proj), capture_output=True)
    run(["init"], tmp, env)
    r = lambda *a: run(["remember"] + list(a), proj, env)
    r("-t", "semantic", "-p", "acme-dashboard", "--kind", "decision", "Billing runs on Stripe webhooks",
      "Invoices are created from the `invoice.paid` webhook, never from the client, so a retried "
      "webhook must stay idempotent: the handler keys on the Stripe event id.")
    r("-t", "procedural", "-p", "acme-dashboard", "Deploys go out behind a flag",
      "Every release ships dark: merge to main deploys to staging, the flag is flipped from the "
      "admin panel after the smoke run. Rollback is the flag, not a revert.")
    r("-t", "episodic", "-p", "acme-dashboard", "--kind", "bugfix", "The nightly export lost rows",
      "The cursor paged by `created_at`, so rows written during the run were skipped. Fixed by "
      "paging on the primary key. Verified by re-running against a seeded copy: 41,802 rows both times.")
    run(["working", "-"], proj, env, stdin="## Goal\nShip the usage-based billing page.\n\n"
        "## Current step\nInvoice totals are off by the proration credit — reproducing against a "
        "staging customer.\n\n## Open questions\n- Does the credit apply before or after tax?\n\n"
        "## Next\n- Backfill the June invoices once the total is right.\n")
    for t in ["Usage-based billing page", "Backfill June invoices", "Drop the legacy CSV export"]:
        run(["task", "add", t], proj, env)
    run(["task", "start", "1"], proj, env)
    run(["task", "block", "2", "--why", "waiting on the proration answer"], proj, env)
    run(["episode", "Traced the off-by-one in invoice totals to the proration credit being applied "
         "after tax; wrote a failing test against a staging customer before touching the math."], proj, env)
    run(["card"], proj, env)
    card = tmp / "vault" / "memory" / "projects" / "acme-dashboard" / "_card.md"
    if card.exists():
        fm, _, _ = card.read_text().partition("\n# ")
        card.write_text(fm + "\n# acme-dashboard\n\n"
                        "**What** Usage-based billing and the customer dashboard (Django + React).\n"
                        "**Run** `make dev` (API on :8000, web on :5173); staging deploys from main.\n"
                        "**Watch out** Invoice math lives in `billing/proration.py` — tax is applied "
                        "last, and the nightly export pages on the primary key, never on `created_at`.\n")
    run(["index", "--quiet"], proj, env)
    return env, proj


def capture(env, proj):
    """Run the real SessionStart hook and take the string it asks Claude Code to inject."""
    hook = json.dumps({"session_id": "demo0001", "cwd": str(proj),
                       "hook_event_name": "SessionStart", "source": "startup"})
    t0 = time.time()
    out = run(["context"], proj, env, stdin=hook)
    secs = time.time() - t0
    text = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    # the throwaway vault lives under a temp dir; show where it would live on a real machine
    text = text.replace(str(Path(env["HUMONA_VAULT"]) / "memory"), "~/claude-brain/memory")
    return text.rstrip("\n").split("\n"), secs


def wrap(lines, cols):
    """Fold long lines the way a terminal would, so nothing runs off the window."""
    out = []
    for line in lines:
        if len(line) <= cols:
            out.append(line)
            continue
        indent = "  " + line[:len(line) - len(line.lstrip())]
        cur, width = line, cols
        while len(cur) > width:
            cut = cur.rfind(" ", 0, width)
            cut = cut if cut > width // 2 else width
            out.append(cur[:cut].rstrip())
            cur, width = indent + cur[cut:].lstrip(), cols
        out.append(cur)
    return out


# ---------- colouring ----------
def spans(line):
    """(text, colour, bold) spans for one payload line — the shapes the hook actually emits."""
    s = line.rstrip()
    if not s:
        return [("", "text", False)]
    if s.startswith("<"):
        return [(s, "tag", False)]
    if s.startswith("## ") or s.startswith("# "):
        return [(s, "title", True)]
    if s.startswith("**") and "**" in s[2:]:
        end = s.index("**", 2) + 2
        return [(s[:end], "amber", True), (s[end:], "text", False)]
    if s.lstrip().startswith("- "):
        ind = s[:len(s) - len(s.lstrip())]
        rest = s.lstrip()[2:]
        head, sep, tail = rest.partition(" — ")
        out = [(ind + "- ", "dim", False), (head, "title", False)]
        if sep:
            out += [(" — ", "dim", False), (tail, "text", False)]
        return out
    if s.startswith("_") and s.endswith("_"):
        return [(s, "dim", False)]
    return [(s, "text", False)]


def draw_window(frame, lines, typed, footer, fonts):
    """One frame: window chrome, the shell lines, the payload so far, the measured footer."""
    from PIL import Image, ImageDraw
    reg, bold = fonts
    h = PAD * 2 + 34 + LH * (len(lines) + len(typed) + (2 if footer else 0))
    img = Image.new("RGB", (W, h), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 34], fill=CHROME)
    for i, col in enumerate(("#f7768e", "#e0af68", "#9ece6a")):
        d.ellipse([PAD + i * 20, 12, PAD + i * 20 + 11, 23], fill=col)
    d.text((W // 2 - 90, 9), "zsh — acme-dashboard", font=reg, fill=C["dim"])
    d.line([0, 34, W, 34], fill=LINE)
    y = 34 + PAD
    for kind, text in lines:
        if kind == "cmd":
            d.text((PAD, y), "$ ", font=bold, fill=C["prompt"])
            d.text((PAD + reg.getlength("$ "), y), text, font=reg, fill=C["text"])
        else:
            d.text((PAD, y), text, font=reg, fill=C[kind])
        y += LH
    for line in typed:
        x = PAD
        for text, col, is_bold in spans(line):
            f = bold if is_bold else reg
            d.text((x, y), text, font=f, fill=C[col])
            x += f.getlength(text)
        y += LH
    if footer:
        y += LH // 2
        d.line([PAD, y, W - PAD, y], fill=LINE)
        d.text((PAD, y + 6), footer, font=reg, fill=C["dim"])
    frame.append(img)
    return img


def build(out_path):
    from PIL import Image
    tmp = Path(tempfile.mkdtemp(prefix="brain-demo-"))
    try:
        env, proj = seed(tmp)
        payload, secs = capture(env, proj)
        chars = sum(len(l) + 1 for l in payload)
        fonts0 = font_pair(FS)
        payload = wrap(payload, int((W - 2 * PAD) // fonts0[0].getlength("x")))
        footer = ("%d chars  ·  ~%d tokens  ·  hook %.2f s  ·  capped at 9,500 chars"
                  % (chars, chars // 4, secs))
        fonts = fonts0
        frames, durations = [], []
        shell = [("cmd", "cd ~/projects/work/acme-dashboard && claude")]
        for n in range(0, len(shell[0][1]) + 1, 3):          # the command types itself
            draw_window(frames, [("cmd", shell[0][1][:n])], [], "", fonts)
            durations.append(40)
        durations[-1] = 500
        head = shell + [("dim", "SessionStart hook  →  humona context  →  injected into the session:")]
        draw_window(frames, head, [], "", fonts)
        durations.append(700)
        for i in range(1, len(payload) + 1):                  # then the real payload arrives
            draw_window(frames, head, payload[:i], "", fonts)
            durations.append(90 if payload[i - 1].strip() else 40)
        draw_window(frames, head, payload, footer, fonts)
        durations.append(4000)
        h = max(f.height for f in frames)
        canvas = [Image.new("RGB", (W, h), BG) for _ in frames]
        for c, f in zip(canvas, frames):
            c.paste(f, (0, 0))
        pal = [c.quantize(colors=64, method=Image.MEDIANCUT, dither=Image.NONE) for c in canvas]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pal[0].save(out_path, save_all=True, append_images=pal[1:], duration=durations,
                    loop=0, optimize=True, disposal=1)
        (out_path.parent / (out_path.stem + "-last.png")).unlink(missing_ok=True)
        print("%s — %d frames, %dx%d, %.1f KB" % (out_path, len(pal), W, h,
                                                  out_path.stat().st_size / 1024))
        print(footer)
        return canvas[-1]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", default=str(REPO / "docs" / "session-start.gif"))
    ap.add_argument("--preview", help="also write the final frame as a PNG here")
    a = ap.parse_args()
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("this dev tool needs Pillow:  pip install pillow", file=sys.stderr)
        return 1
    last = build(Path(a.out))
    if a.preview:
        last.save(a.preview)
        print("preview →", a.preview)
    return 0


if __name__ == "__main__":
    sys.exit(main())
