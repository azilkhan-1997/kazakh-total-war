# Reviewed source texture import

This one-time GitHub Actions workflow restores exactly **19 PNG source textures**
from Millennium A.D. commit `91636b405ee8d0088ec3a34fba6074dbd5c9d0f3`.
It does not import runtime packages, EXE/DLL files, a source ZIP or diagnostic logs.
The two project-owned gzip logs are handled separately by the source publisher.

The fixed allowlist includes exact size/SHA-256 values and is checked against
both the per-file source manifest and the fresh distribution audit. Original
CC-BY-SA-3.0 license bytes, authorship and source notices must remain present.
Every needed download is verified before any destination is written. Existing
files with different bytes, symlinks and unexpected paths stop the import.

Run without changing the working tree:

```bash
python3 build/source_import/test_source_import.py
python3 build/source_import/import_source.py --verify-downloads
```

`--apply` restores missing verified textures locally without making a Git commit.
`--publish --expected-head <40-character SHA>` additionally requires a clean
checkout of that SHA, the fixed GitHub origin and an unchanged `main` tip. It
stages only the missing allowlisted PNG additions and checks their exact staged
Git blob hashes. The resulting commit has the supplied SHA as its sole parent.
Publication uses a normal non-force push, with remote-tip checks before writes,
commit and push. A concurrent advance fails rather than rebasing or forcing.

The workflow can be dispatched on `main`, or runs when its own YAML path is
published to `main`. Its texture-only commit cannot trigger itself. A repeated
run verifies existing hashes and returns without downloads, writes or a commit.
The token is exposed only to the publication step and passed to Git through a
temporary process environment header; it is not put into a URL or source file.

Portable tests use synthetic PNG fixtures with mocked transport and temporary
Git repositories. They do not publish to GitHub. Successful local verification
does not mean the workflow or a public push has been executed.
