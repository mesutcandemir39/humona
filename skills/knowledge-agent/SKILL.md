---
name: knowledge-agent
description: Build a queryable knowledge base from documents (docs folders, notes, exported text) and answer from it.
---
# knowledge-agent
1. Ingest: `humona ingest <file|dir> --name <corpus>` (md/txt/rst/html/csv; secrets redacted; re-running rebuilds the corpus).
   PDFs/DOCX: convert to text first (e.g. `textutil -convert txt` on macOS, `pdftotext`), then ingest.
2. Query: `humona search -t knowledge "<question in English>" -k 5` → `humona recall <path>` for the best 1-3 chunks.
3. Answer only from retrieved chunks; cite `source:` from frontmatter. If not covered, say so.
Corpora live in `memory/knowledge/<corpus>/` and sync like other memory — use `--private`-style care: don't ingest secrets or personal data you don't want on GitHub.
