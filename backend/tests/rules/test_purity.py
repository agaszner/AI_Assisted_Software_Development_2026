"""Golden rule 4: rules/ must not import Django, the DB, the network or read the system clock."""

import ast
from pathlib import Path

RULES = Path(__file__).resolve().parents[2] / "rules"
FORBIDDEN_MODULES = {"django", "core", "banking", "plans", "api", "socket", "urllib", "http"}
CLOCK_CALLS = {"now", "today", "utcnow"}


def imported_modules(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
    return names


def clock_calls(tree: ast.AST) -> list[str]:
    calls = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in CLOCK_CALLS
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in {"date", "datetime", "timezone"}
        ):
            calls.append(f"{node.func.value.id}.{node.func.attr}()")
    return calls


def test_rules_package_is_pure() -> None:
    files = sorted(RULES.glob("*.py"))
    assert files, "rules/ has no modules"
    for file in files:
        tree = ast.parse(file.read_text())
        for module in imported_modules(tree):
            assert module.split(".")[0] not in FORBIDDEN_MODULES, f"{file.name} imports {module}"
        assert clock_calls(tree) == [], f"{file.name} reads the system clock"
