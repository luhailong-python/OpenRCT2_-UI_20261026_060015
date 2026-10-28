"""Validate migrated project associations without changing any files.

This legacy entry point now reads only this project's canonical association
record. Historical source links are checked as text and are never opened.
"""

from collections import Counter
from pathlib import Path
import re
import sys


ROOT = Path(__file__).parent.parent
EXPECTED_SOURCE_READMES = (
    "designs/mail-ui-v1/README.md",
    "designs/team-ui-v2/README.md",
)
SOURCE_RECORD = re.compile(r"^原记录位置：\[([^\]\r\n]+)\]\([^\r\n]+\)[ \t]*$", re.MULTILINE)


def main(root: Path | None = None) -> int:
    """Check the local record; an alternate root supports isolated validation."""
    project_root = Path(root) if root is not None else ROOT
    record = project_root / "docs" / "image-reference-associations.md"
    try:
        text = record.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        print(f"Association validation failed: cannot read {record}: {exc}", file=sys.stderr)
        return 1

    counts = Counter(SOURCE_RECORD.findall(text))
    missing = [source for source in EXPECTED_SOURCE_READMES if not counts[source]]
    duplicates = sorted(source for source, count in counts.items() if count > 1)
    if missing or duplicates:
        print(f"Association validation failed: {record}", file=sys.stderr)
        for source in missing:
            print(f"Missing source README record: {source}", file=sys.stderr)
        for source in duplicates:
            print(f"Duplicate source README record ({counts[source]}): {source}", file=sys.stderr)
        return 1

    print(f"Validated {len(EXPECTED_SOURCE_READMES)} source README associations in {record}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
