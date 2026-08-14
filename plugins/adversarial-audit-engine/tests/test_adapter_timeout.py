"""test_adapter_timeout.py — the eye's HTTP timeout is generous by default and configurable.

A real run timed out mid-review at the old 60s ceiling because a LOCAL Ollama eye is slow on a big
audit payload. The default is now 300s (audits are not latency-sensitive), overridable via
AAE_EYE_TIMEOUT or a constructor arg.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from aae.adapters import OpenAICompatibleClient  # noqa: E402


class AdapterTimeout(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.get("AAE_EYE_TIMEOUT")
        os.environ.pop("AAE_EYE_TIMEOUT", None)

    def tearDown(self):
        if self._saved is None:
            os.environ.pop("AAE_EYE_TIMEOUT", None)
        else:
            os.environ["AAE_EYE_TIMEOUT"] = self._saved

    def test_default_is_generous(self):
        c = OpenAICompatibleClient(model="m", base_url="http://localhost:11434/v1")
        self.assertEqual(c.timeout, 300)

    def test_env_override(self):
        os.environ["AAE_EYE_TIMEOUT"] = "120"
        c = OpenAICompatibleClient(model="m", base_url="http://localhost:11434/v1")
        self.assertEqual(c.timeout, 120)

    def test_param_beats_env(self):
        os.environ["AAE_EYE_TIMEOUT"] = "120"
        c = OpenAICompatibleClient(model="m", base_url="http://localhost:11434/v1", timeout=42)
        self.assertEqual(c.timeout, 42)

    def test_bad_env_falls_back(self):
        os.environ["AAE_EYE_TIMEOUT"] = "not-a-number"
        c = OpenAICompatibleClient(model="m", base_url="http://localhost:11434/v1")
        self.assertEqual(c.timeout, 300)


if __name__ == "__main__":
    unittest.main()
