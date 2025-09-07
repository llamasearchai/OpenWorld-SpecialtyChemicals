from __future__ import annotations

import re
import sys
from pathlib import Path


def replace(pattern: str, repl: str, path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    new = re.sub(pattern, repl, text, flags=re.MULTILINE)
    if new == text:
        print(f"No change in {path}")
    else:
        path.write_text(new, encoding="utf-8")
        print(f"Updated {path}")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/release_bump.py <version>")
        return 2
    version = sys.argv[1]

    # Update pyproject.toml
    replace(r"^version\s*=\s*\"[^\"]+\"", f"version = \"{version}\"", Path("pyproject.toml"))

    # Update package __init__.py
    pkg_init = Path("openworld_specialty_chemicals/__init__.py")
    replace(r"^__version__\s*=\s*\"[^\"]+\"", f"__version__ = \"{version}\"", pkg_init)

    # Update CHANGELOG header (insert new section stub at top)
    ch = Path("CHANGELOG.md")
    if ch.exists():
        content = ch.read_text(encoding="utf-8")
        if f"## [{version}]" not in content:
            ch.write_text(
                f"## [{version}] - YYYY-MM-DD\n- Describe changes here.\n\n" + content,
                encoding="utf-8",
            )
            print("Prepended new changelog section")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

