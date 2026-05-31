"""Rotate the changelog as part of a release.

Usage:
    python scripts/release_changelog.py <version> [<date>] [--notes <path>]

Given the current ``CHANGELOG.md`` (the changes accumulated for this release), this:

  * writes the release-notes body (changelog minus HTML comments) to ``--notes`` (default
    ``release_notes.md``) for use as the GitHub release body;
  * prepends a ``## <version> - <date>`` section with that body to ``CHANGELOG_HISTORY.md``
    (newest first, right after the title);
  * resets ``CHANGELOG.md`` to its empty template for the next cycle.

The repository root is taken as the parent of this script's directory, so it can be run from
anywhere.
"""
from __future__ import annotations

import argparse
import re
from datetime import date as date_cls
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHANGELOG_TEMPLATE = (
    "<!-- Changes for the NEXT release. Add bullet points here as you make changes.\n"
    "     On release this becomes the release notes, is appended to CHANGELOG_HISTORY.md\n"
    "     under a version heading, and this file is emptied automatically. -->\n"
)


def changelog_body(text: str) -> str:
    """Return the changelog text with HTML comments stripped and surrounding whitespace removed."""
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL).strip()


def prepend_history(history: str, version: str, date: str, body: str) -> str:
    """Insert a new version section just after the first heading line of the history document."""
    section = f"## {version} - {date}\n\n{body}\n"
    lines = history.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            insert_at = i + 1
            break
    head = "\n".join(lines[:insert_at]).rstrip()
    tail = "\n".join(lines[insert_at:]).strip()
    parts = [part for part in (head, section.strip(), tail) if part]
    return "\n\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("date", nargs="?", default=None)
    parser.add_argument("--notes", default=str(ROOT / "release_notes.md"))
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()

    root = Path(args.root)
    changelog = root / "CHANGELOG.md"
    history = root / "CHANGELOG_HISTORY.md"
    date = args.date or date_cls.today().isoformat()

    body = changelog_body(changelog.read_text(encoding="utf-8"))
    if not body:
        raise SystemExit("CHANGELOG.md has no entries to release.")

    Path(args.notes).write_text(body + "\n", encoding="utf-8")
    history.write_text(
        prepend_history(history.read_text(encoding="utf-8"), args.version, date, body),
        encoding="utf-8",
    )
    changelog.write_text(CHANGELOG_TEMPLATE, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
