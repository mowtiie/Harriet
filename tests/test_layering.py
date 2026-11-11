"""Checks that packages only depend on the layers below them (see CLAUDE.md)."""

import ast
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURES = sorted(path.name for path in (ROOT / "features").iterdir() if path.is_dir())
FEATURES = [name for name in FEATURES if not name.startswith("_")]


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module)
    return modules


def violations(package_dir: Path, forbidden_roots: set[str], forbidden_features: set[str]) -> list[str]:
    found = []
    for path in sorted(package_dir.rglob("*.py")):
        for module in sorted(imported_modules(path)):
            parts = module.split(".")
            blocked = parts[0] in forbidden_roots or (
                parts[0] == "features" and len(parts) > 1 and parts[1] in forbidden_features
            )
            if blocked:
                label = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name
                found.append(f"{label} imports {module}")
    return found


class LayeringTests(unittest.TestCase):
    def test_features_were_found(self) -> None:
        self.assertIn("playback", FEATURES)
        self.assertGreaterEqual(len(FEATURES), 9)

    def test_core_depends_on_nothing_above_it(self) -> None:
        found = violations(
            ROOT / "core", {"cogs", "views", "features", "config", "bot"}, set()
        )
        self.assertEqual(found, [])

    def test_shared_views_do_not_depend_on_features_or_cogs(self) -> None:
        found = violations(ROOT / "views", {"cogs", "features", "bot"}, set())
        self.assertEqual(found, [])

    def test_features_do_not_depend_on_cogs_or_each_other(self) -> None:
        found = []
        for name in FEATURES:
            others = set(FEATURES) - {name}
            found += violations(ROOT / "features" / name, {"cogs", "bot"}, others)
        self.assertEqual(found, [])


class CheckerTests(unittest.TestCase):
    def check(self, source: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "module.py").write_text(source, encoding="utf-8")
            found = violations(Path(directory), {"cogs"}, {"playback"})
        return [line.split(" imports ")[1] for line in found]

    def test_catches_forbidden_imports_in_every_form(self) -> None:
        source = "import cogs.fun\nfrom cogs import help\nfrom features.playback import player\n"
        self.assertEqual(self.check(source), ["cogs", "cogs.fun", "features.playback"])

    def test_allows_other_imports(self) -> None:
        source = "import os\nfrom features.games import rps\nfrom core.errors import UserError\n"
        self.assertEqual(self.check(source), [])


if __name__ == "__main__":
    unittest.main()
