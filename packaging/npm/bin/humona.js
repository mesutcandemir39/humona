#!/usr/bin/env node
// The engine is one Python file; this wrapper is the shortest honest path from `npx humona` to it.
//
// The package carries the same mini-checkout the PyPI wheel does, at `_payload/`, so the engine
// finds `skills/`, `setup/` and `hooks/` where it expects them — one level up from itself. All this
// does is choose an interpreter, hand over argv, and pass the exit code back. No postinstall step:
// nothing is compiled or downloaded, so there is nothing to do at install time, and a postinstall
// that wired hooks behind the user's back would be the wrong default anyway.
"use strict";

const { spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const ENGINE = path.join(__dirname, "..", "_payload", "engine", "humona.py");
const MIN = [3, 8];

// Windows ships `py`, most else ships `python3`; `python` is last because on some systems it is 2.7.
const CANDIDATES = process.platform === "win32"
  ? [["py", ["-3"]], ["python", []], ["python3", []]]
  : [["python3", []], ["python", []]];

function version(cmd, pre) {
  const r = spawnSync(cmd, pre.concat(["-c", "import sys; print('%d.%d' % sys.version_info[:2])"]),
                      { encoding: "utf8" });
  if (r.status !== 0 || !r.stdout) return null;
  const parts = r.stdout.trim().split(".").map(Number);
  if (parts.length !== 2 || parts.some(Number.isNaN)) return null;
  return parts;
}

function interpreter() {
  for (const [cmd, pre] of CANDIDATES) {
    const v = version(cmd, pre);
    if (v && (v[0] > MIN[0] || (v[0] === MIN[0] && v[1] >= MIN[1]))) return [cmd, pre];
  }
  return null;
}

if (!fs.existsSync(ENGINE)) {
  process.stderr.write("humona: the engine is missing from this package (" + ENGINE + ").\n" +
                       "Reinstall with: npm install -g humona\n");
  process.exit(1);
}

const found = interpreter();
if (!found) {
  process.stderr.write(
    "humona needs Python " + MIN.join(".") + " or newer on PATH, and did not find it.\n\n" +
    "  macOS     brew install python\n" +
    "  Debian    sudo apt install python3\n" +
    "  Windows   winget install Python.Python.3.12\n\n" +
    "The engine is a single standard-library Python file — there is nothing else to install.\n");
  process.exit(1);
}

const [cmd, pre] = found;
const r = spawnSync(cmd, pre.concat([ENGINE], process.argv.slice(2)), { stdio: "inherit" });
if (r.error) {
  process.stderr.write("humona: could not start " + cmd + ": " + r.error.message + "\n");
  process.exit(1);
}
// A signal death has no exit code; report it the way a shell does so CI sees a failure.
process.exit(r.status === null ? 128 + (r.signal === "SIGINT" ? 2 : 15) : r.status);
