"""test_eye.py — the free level-3 independent eye is wired from the environment, not narrated.

`external_eye_from_env` turns AAE_EYE=groq|ollama|openrouter (or an explicit base_url) into an adapter
whose identity is a genuinely different vendor -> independence level 3. Not configured -> None (the run
stays level 1 and says so). The eye is credited only once actually called; this test covers the wiring,
not the network call.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from aae import external_eye_from_env, independence_level_between  # noqa: E402


class EyeFromEnv(unittest.TestCase):
    def test_presets_reach_level_3(self):
        for preset in ("groq", "ollama", "openrouter"):
            eye = external_eye_from_env({"AAE_EYE": preset, "AAE_EYE_KEY": "x"})
            self.assertIsNotNone(eye, preset)
            lvl = int(independence_level_between("anthropic:claude-opus", eye.identity))
            self.assertEqual(3, lvl, f"{preset} should be a different vendor -> level 3")

    def test_not_configured_returns_none(self):
        self.assertIsNone(external_eye_from_env({}))

    def test_explicit_base_url_overrides(self):
        eye = external_eye_from_env({"AAE_EYE_BASE_URL": "http://localhost:1234/v1",
                                     "AAE_EYE_MODEL": "qwen2.5", "AAE_EYE_KEY": "x"})
        self.assertIsNotNone(eye)
        self.assertIn("qwen2.5", eye.identity)

    def test_ollama_defaults_its_key(self):
        # a local server needs no real key; the preset supplies one
        eye = external_eye_from_env({"AAE_EYE": "ollama"})
        self.assertIsNotNone(eye)
        self.assertTrue(eye.identity.startswith("ollama-local:"))


if __name__ == "__main__":
    unittest.main()
