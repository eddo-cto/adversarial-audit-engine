"""
test_invariant_version.py — the release surface must agree with itself.

This is a REGRESSION test for a real, shipped defect: `aae.__version__` said
0.6.0 while plugin.json and marketplace.json said 0.12.0 and the README said
0.8.0. Four declarations of the same fact, three of them wrong. In the engine's
own taxonomy that is a NON_LOCAL_MECHANICAL finding (two sections, incompatible
values) — exactly the class the engine claims high recall on. It should not be
able to happen again silently.
"""

import json
import os
import re
import sys
import unittest

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(PLUGIN_DIR))
sys.path.insert(0, PLUGIN_DIR)

import aae  # noqa: E402


def _json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class VersionCoherence(unittest.TestCase):
    """One fact, four places: they must all say the same thing."""

    def test_package_matches_plugin_manifest(self):
        manifest = _json(os.path.join(PLUGIN_DIR, ".claude-plugin", "plugin.json"))
        self.assertEqual(
            aae.__version__, manifest["version"],
            "aae.__version__ and plugin.json disagree: whoever imports the "
            "package reads a different version from whoever installs it.",
        )

    def test_plugin_manifest_matches_marketplace(self):
        manifest = _json(os.path.join(PLUGIN_DIR, ".claude-plugin", "plugin.json"))
        market = _json(os.path.join(REPO_ROOT, ".claude-plugin", "marketplace.json"))
        entry = next(p for p in market["plugins"]
                     if p["name"] == "adversarial-audit-engine")
        self.assertEqual(manifest["version"], entry["version"])

    def test_readme_status_matches_package(self):
        with open(os.path.join(REPO_ROOT, "README.md"), encoding="utf-8") as fh:
            readme = fh.read()
        m = re.search(r"Status: research preview \(v([0-9][0-9.]*)\)", readme)
        self.assertIsNotNone(m, "README lost its status line")
        self.assertEqual(
            m.group(1), aae.__version__,
            "the README advertises a different version than the code ships",
        )

    def test_version_is_parseable_semver(self):
        self.assertRegex(aae.__version__, r"^\d+\.\d+\.\d+$")


class PublicSurface(unittest.TestCase):
    """Everything __all__ promises must actually exist, and the deterministic
    controls added in 0.7.0-0.12.0 must be reachable from the package root.
    They were previously importable only by explicit submodule path, so the
    best features of the engine were invisible to anyone exploring the API."""

    NEW_CONTROLS = [
        "grounding", "criterion", "evidence_pairing", "negation_spectrometry",
        "support_geometry", "repr_validator", "run_metrics", "usage_ledger",
        "legal_oracle", "normattiva_fetcher",
    ]

    def test_all_declared_symbols_exist(self):
        missing = [n for n in aae.__all__ if not hasattr(aae, n)]
        self.assertEqual([], missing, f"__all__ promises absent names: {missing}")

    def test_new_controls_reachable_from_root(self):
        for name in self.NEW_CONTROLS:
            with self.subTest(module=name):
                self.assertTrue(hasattr(aae, name),
                                f"`from aae import {name}` does not work")
                self.assertIn(name, aae.__all__)

    def test_every_submodule_imports_cleanly(self):
        import pkgutil
        import importlib
        for mod in pkgutil.iter_modules(aae.__path__):
            with self.subTest(module=mod.name):
                importlib.import_module(f"aae.{mod.name}")

    def test_core_has_no_hard_third_party_dependency(self):
        """The project's claim is that the core runs anywhere, stdlib-only.

        Only MODULE-LEVEL imports count: a lazy import inside a function (as
        `AnthropicLLMClient.__init__` does with `anthropic`) is an OPTIONAL
        dependency — importing the package still works without it, which is
        exactly the contract. Flagging those would be a false positive, and
        this suite is not allowed to make the mistake the engine exists to
        prevent."""
        import ast
        import pkgutil
        stdlib = set(sys.stdlib_module_names)
        offenders = []
        for mod in pkgutil.iter_modules(aae.__path__):
            path = os.path.join(PLUGIN_DIR, "aae", f"{mod.name}.py")
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            for node in tree.body:  # top level only — not ast.walk
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [(node.module or "").split(".")[0]]
                else:
                    continue
                for n in names:
                    if n and n not in stdlib and n != "aae":
                        offenders.append(f"{mod.name}.py -> {n}")
        self.assertEqual([], offenders,
                         f"hard non-stdlib imports in the core: {offenders}")

    def test_importing_the_package_needs_no_optional_dependency(self):
        """The behavioural counterpart of the test above: `import aae` must
        succeed in a clean interpreter with nothing installed."""
        import subprocess
        proc = subprocess.run(
            [sys.executable, "-c", "import aae; print(aae.__version__)"],
            capture_output=True, text=True,
            env={**os.environ, "PYTHONPATH": PLUGIN_DIR},
        )
        self.assertEqual(0, proc.returncode, proc.stderr)


if __name__ == "__main__":
    unittest.main()
