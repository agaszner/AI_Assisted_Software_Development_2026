#!/usr/bin/env python3
"""Documentation consistency check (AGENTS.md section 8.6). Standard library only.

Fails when:
- an AC in docs/specification.md has no row in docs/traceability.md;
- a row whose status is not "planned" references a test that does not exist
  (paths are relative to backend/);
- frontend references (frontend/...test.tsx::title) must name an existing file and test title.
- files under backend/ or frontend/src/ have uncommitted changes but CHANGELOG.md has none.

Limitation: the CHANGELOG rule only sees uncommitted changes, so it checks the change
about to be committed.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
TEST_REF = re.compile(r"tests/[\w/]+\.py(?:::\w+)?")
FRONTEND_REF = re.compile(r"frontend/[\w/.-]+\.(?:test|spec)\.tsx?(?:::\w+)?")


def spec_acs() -> set[str]:
    return set(re.findall(r"\*\*(AC\d+)\*\*", (ROOT / "docs/specification.md").read_text()))


def traceability_rows() -> list[tuple[str, str, str]]:
    """Return (ac, evidence, status) for every AC row of the traceability table."""
    rows = []
    for line in (ROOT / "docs/traceability.md").read_text().splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 5 and re.fullmatch(r"AC\d+", cells[0]):
            rows.append((cells[0], cells[3], cells[4]))
    return rows


def test_reference_exists(ref: str) -> bool:
    """Backend refs are relative to backend/ and name a `def`; frontend refs are relative to the
    repository root and name a quoted Vitest / Playwright test title."""
    path, _, name = ref.partition("::")
    in_frontend = path.startswith("frontend/")
    file = (ROOT if in_frontend else BACKEND) / path
    if not file.is_file():
        return False
    if not name:
        return True
    if in_frontend:
        pattern = rf"""["']{re.escape(name)}["']"""
    else:
        pattern = rf"^\s*def {re.escape(name)}\("
    return re.search(pattern, file.read_text(), re.MULTILINE) is not None


def changed_paths() -> set[str]:
    out = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return {line[3:].split(" -> ")[-1] for line in out.splitlines()}


def main() -> int:
    errors = []
    rows = traceability_rows()
    for ac in sorted(spec_acs() - {row[0] for row in rows}, key=lambda a: int(a[2:])):
        errors.append(f"{ac} has no row in docs/traceability.md")
    for ac, evidence, status in rows:
        if status == "planned":
            continue
        for ref in TEST_REF.findall(evidence) + FRONTEND_REF.findall(evidence):
            if not test_reference_exists(ref):
                errors.append(f"{ac}: referenced test not found: {ref}")
    changed = changed_paths()
    code_changed = any(p.startswith(("backend/", "frontend/src/")) for p in changed)
    if code_changed and "CHANGELOG.md" not in changed:
        errors.append("backend/ or frontend/src/ changed without a CHANGELOG.md change")
    for error in errors:
        print(f"docs-check: {error}", file=sys.stderr)
    if not errors:
        print("docs-check: OK")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
