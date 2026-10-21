# Accessibility

This project has no graphical interface. It is a command-line tool whose output is plain text,
and a vault of Markdown files you read in whatever editor you already use. Most of what follows
is a consequence of that, and the rest is written down so you know what is not solved yet.

## What is already true

- **Nothing depends on colour.** The engine emits no ANSI escape sequences at all, so every
  distinction it makes — `OK` versus `FAIL`, a heading, a hit — is carried by words, not by hue.
  There is no "colourblind mode" because there is no colour to adapt.
- **Output is linear text**, written to stdout in reading order. No box drawing, no cursor
  positioning, no spinners, no progress bars that overwrite themselves — a screen reader or a
  braille display reads it the way it arrives, and piping it to a file loses nothing.
- **Memory is Markdown.** Notes are plain UTF-8 files with YAML frontmatter and `[[wikilinks]]`.
  Any editor, `cat`, `grep` or a screen reader handles them. No proprietary viewer stands between
  you and your own notes, and Obsidian is optional.
- **It never blocks on input it was not given.** Every prompt checks `isatty()` first, so running
  under automation, a hook, or a session driven by assistive software will not leave the terminal
  waiting on a question nobody can see.
- **Nothing is time-limited.** There is no interaction you have to complete before a timeout.
- **Generated documents are structured**: real headings, lists and links rather than text that
  merely looks arranged, so heading navigation works in `index.md`, `board.md` and the per-layer
  `MEMORY.md` files.

## Known limitations

Honest list; each is a thing we would fix given a report that it matters to someone.

- **Unicode symbols appear in output.** An arrow (`→`) marks where a note was written, a bullet
  (`·`) separates fields, an em dash separates a title from its summary, and `humona board` marks
  a blocked task with `⛔`. Some screen readers announce these verbosely, some skip them. There is
  no ASCII-only output mode yet.
- **Tabular output is aligned with spaces**, not marked up as a table, so `humona doctor` and
  `humona board` read as lines rather than as cells with headers.
- **Install instructions assume a terminal.** There is no graphical installer, and the plugin
  install happens inside Claude Code, whose own accessibility is Anthropic's to document.
- **The optional Obsidian workflow is out of our hands.** If you use Obsidian as a viewer, its
  accessibility is Obsidian's; nothing here requires it.

## Reporting a barrier

If something here is unusable with the tools you rely on, that is a bug and it is wanted:

- Open an issue: https://github.com/mesutcandemir39/humona/issues
- Or message the maintainer on Telegram: [@mesutcan](https://t.me/mesutcan)

Say what you use (screen reader, braille display, magnifier, voice control, a particular
terminal), what you ran, and what happened instead of what you expected. A report naming one
concrete command is worth more than a general statement, and will be treated as a defect rather
than a feature request.
