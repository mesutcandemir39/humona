#!/usr/bin/env python3
"""Install humona on this machine (macOS / Linux / Windows). Idempotent — safe to re-run.

  git clone https://github.com/mesutcandemir39/humona.git ~/humona-src
  python3 ~/humona-src/setup/install.py
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]      # the code checkout
ENGINE = REPO / "engine" / "humona.py"


def pick_vault():
    """Where the user's memory goes. Kept out of the code checkout for a reason: the code is a
    public repo that `humona upgrade` fast-forwards, and anything inside it risks being published
    by a `git push` to a fork. Order: --vault, an earlier install's choice, an existing vault in
    this checkout (installs made before the split), then the documented default.
    """
    if "--vault" in sys.argv:
        return Path(sys.argv[sys.argv.index("--vault") + 1]).expanduser().resolve()
    out = subprocess.run([sys.executable, str(ENGINE), "vault"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("vault:") and "installer config" in out:
            return Path(line.split(":", 1)[1].split("   (")[0].strip()).expanduser().resolve()
    if any((REPO / "memory").rglob("*.md")):
        return REPO
    return (Path.home() / "humona" / "vault").resolve()


VAULT = pick_vault()
WORKSPACE = VAULT.parent
MEM = VAULT / "memory"
SPLIT = VAULT != REPO
HOME = Path.home()
CLAUDE = HOME / ".claude"
BIN = HOME / ".local" / "bin"
WIN = os.name == "nt"
START, END = "<!-- humona:start -->", "<!-- humona:end -->"
OLD_START, OLD_END = "<!-- brain:start -->", "<!-- brain:end -->"   # before the 3.0 rename
CLI_NAMES = ("humona", "brain")   # the product, and the alias an older install already has


def install_cli():
    BIN.mkdir(parents=True, exist_ok=True)
    py = Path(sys.executable).as_posix()
    if WIN:
        for name in CLI_NAMES:
            (BIN / (name + ".cmd")).write_text('@"%s" "%s" %%*\n' % (sys.executable, ENGINE))
            (BIN / name).write_text('#!/bin/sh\nexec "%s" "%s" "$@"\n' % (py, ENGINE.as_posix()))  # Git Bash
        path = subprocess.run(["powershell", "-NoProfile", "-Command", "[Environment]::GetEnvironmentVariable('Path','User')"],
                              capture_output=True, text=True).stdout.strip()
        if str(BIN).lower() not in path.lower():
            subprocess.run(["powershell", "-NoProfile", "-Command",
                            "[Environment]::SetEnvironmentVariable('Path', '%s;' + [Environment]::GetEnvironmentVariable('Path','User'), 'User')" % BIN])
            print("added %s to user PATH (restart terminal)" % BIN)
    else:
        ENGINE.chmod(0o755)
        for name in CLI_NAMES:
            link = BIN / name
            if link.is_symlink() or link.exists():
                link.unlink()
            link.symlink_to(ENGINE)
    print("cli:", ", ".join(str(BIN / (n + ".cmd" if WIN else n)) for n in CLI_NAMES))


def hook_cmd(arg):
    return '"%s" "%s" %s' % (Path(sys.executable).as_posix(), ENGINE.as_posix(), arg)


def merge_settings():
    f = CLAUDE / "settings.json"
    CLAUDE.mkdir(exist_ok=True)
    s = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    if f.exists():
        shutil.copy(f, f.with_suffix(".json.bak"))
    s["autoMemoryDirectory"] = (MEM / "3-LongTerm" / "Core").as_posix()
    s["autoDreamEnabled"] = True
    mem_rule = "//" + MEM.as_posix().lstrip("/")
    allow = s.setdefault("permissions", {}).setdefault("allow", [])
    for r in ("Bash(humona *)", "Bash(brain *)", "Read(%s/**)" % mem_rule, "Edit(%s/**)" % mem_rule):
        if r not in allow:
            allow.append(r)
    hooks = s.setdefault("hooks", {})
    # (event, matcher, humona command, timeout, async) — several per event allowed:
    # `hint` must be synchronous because its stdout is what reaches the model as context.
    ours = [
        ("SessionStart", None, "context", 15, False),
        ("UserPromptSubmit", None, "hint", 6, False),
        ("UserPromptSubmit", None, "sense", 5, True),
        ("PostToolUse", "Edit|Write|MultiEdit|NotebookEdit|Bash", "sense", 5, True),
        ("PostToolUseFailure", ".*", "sense", 5, True),
        ("PreCompact", None, "consolidate --quiet", 30, False),
        ("SessionEnd", None, "consolidate --quiet", 40, False),
    ]
    for event in dict.fromkeys(e for e, *_ in ours):  # drop our old groups, keep the user's
        hooks[event] = [g for g in hooks.get(event, [])
                        if not any(("humona" in h.get("command", "") or "brain" in h.get("command", ""))
                                   for h in g.get("hooks", []))]
    for event, matcher, arg, timeout, is_async in ours:
        h = {"type": "command", "command": hook_cmd(arg), "timeout": timeout}
        if is_async:
            h["async"] = True
        g = {"matcher": matcher, "hooks": [h]} if matcher else {"hooks": [h]}
        hooks[event] = hooks.get(event, []) + [g]
    f.write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("settings:", f)


def obsidian_ignore():
    """What Obsidian should hide. Split install: the vault is opened directly, so only the layers
    that are not knowledge. Single-directory install: also every code folder sitting next to it."""
    if SPLIT:
        return ["memory/private/", "memory/Archive/"]
    # a single-directory install from before 3.0: the code sits next to memory/ in `brain/`
    return ["brain/engine/", "brain/setup/", "brain/skills/", "brain/tests/", "brain/.github/",
            "brain/README.md", "brain/CHANGELOG.md", "brain/CLAUDE.md", "brain/LICENSE",
            "projects/", "brain/memory/private/", "brain/memory/Archive/"]


OBSIDIAN_IGNORE = obsidian_ignore()


def configure_obsidian():
    """Tell Obsidian to ignore the code: only `memory/` is knowledge.

    Without this the graph view fills with README and SKILL files that nothing links to, and
    search returns the engine's own documentation instead of notes.
    """
    cfg = (VAULT if SPLIT else WORKSPACE) / ".obsidian" / "app.json"
    if not cfg.parent.is_dir():
        return  # the vault has never been opened in Obsidian on this machine
    data = {}
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except ValueError:
            data = {}
    keep = [f for f in data.get("userIgnoreFilters", []) if f not in OBSIDIAN_IGNORE]
    data["userIgnoreFilters"] = keep + OBSIDIAN_IGNORE
    cfg.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("obsidian:", cfg, "(%d ignore filters)" % len(data["userIgnoreFilters"]))


def install_claude_md():
    f = CLAUDE / "CLAUDE.md"
    block = "%s\n%s\n%s" % (START, (REPO / "setup" / "CLAUDE.md").read_text(encoding="utf-8").strip(), END)
    text = f.read_text(encoding="utf-8") if f.exists() else ""
    for a, b in ((START, END), (OLD_START, OLD_END)):   # replace ours, and the pre-3.0 block
        if a in text and b in text:
            text = text[: text.index(a)] + block + text[text.index(b) + len(b):]
            break
    else:
        text = (text.rstrip() + "\n\n" + block).lstrip()
    f.write_text(text + "\n", encoding="utf-8")
    print("CLAUDE.md:", f)


def install_skills():
    """Copy repo skills into ~/.claude/skills (copy, not symlink: works on Windows without admin)."""
    dst_root = CLAUDE / "skills"
    src_root = REPO / "skills"
    names = {p.name for p in src_root.iterdir() if (p / "SKILL.md").exists()} if src_root.exists() else set()
    if dst_root.exists():  # drop skills we installed earlier that no longer exist in the repo
        for d in dst_root.iterdir():
            if (d / ".brain-managed").exists() and d.name not in names:
                shutil.rmtree(d)
    for n in sorted(names):
        d = dst_root / n
        if d.exists() and not (d / ".brain-managed").exists():
            print("skip skill %s: a user skill with that name exists" % n)
            continue
        if d.exists():
            shutil.rmtree(d)
        shutil.copytree(src_root / n, d)
        (d / ".brain-managed").write_text("installed by brain setup; edit in the brain repo\n")
    print("skills:", ", ".join(sorted(names)))


def prepare_vault():
    """Create the vault, record it for the engine, and give it a local git history.

    `git init` with no remote on purpose: the user gets undo and a record of every change, and
    nothing can be published until they add a remote themselves. `brain sync` commits locally and
    stops there while origin is missing.
    """
    MEM.mkdir(parents=True, exist_ok=True)
    if SPLIT:
        subprocess.run([sys.executable, str(ENGINE), "vault", str(VAULT)], stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, str(ENGINE), "init"], stdout=subprocess.DEVNULL,
                   env=dict(os.environ, HUMONA_VAULT=str(VAULT)))
    if not (VAULT / ".git").exists() and shutil.which("git"):
        subprocess.run(["git", "init", "-q", str(VAULT)])
        (VAULT / ".gitignore").write_text("memory/private/\n.obsidian/workspace.json\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(VAULT), "add", "-A"], stdout=subprocess.DEVNULL)
        subprocess.run(["git", "-C", str(VAULT), "commit", "-q", "-m", "brain: empty vault"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("vault:", VAULT)


def main():
    global print
    if "--quiet" in sys.argv:
        print = lambda *a, **k: None  # noqa: E731
    if sys.version_info < (3, 8):
        sys.exit("Python 3.8+ required")
    prepare_vault()
    install_cli()
    merge_settings()
    install_claude_md()
    install_skills()
    configure_obsidian()
    projects = WORKSPACE / "projects"
    projects.mkdir(parents=True, exist_ok=True)
    print("projects folder:", projects)
    print("")
    print("done. three things, then you are set up:")
    print("  1. restart Claude Code (the hooks are read at startup)")
    print("  2. run:  humona doctor        — every check must pass")
    print("  3. optional: open %s as an Obsidian vault to see your memory" % (VAULT if SPLIT else WORKSPACE))
    print("")
    print("your notes stay on this machine. to sync them between machines, create a PRIVATE repo")
    print("and point the vault at it:  git -C %s remote add origin <your-private-repo>" % VAULT)
    print("engine updates later:  humona upgrade")


if __name__ == "__main__":
    main()
