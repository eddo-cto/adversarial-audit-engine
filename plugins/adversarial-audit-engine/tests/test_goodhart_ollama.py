"""
test_goodhart_ollama.py — the live transport's assembly/parse (no network) and the pilot runner wiring.

Pins:
  1. parse_chat_response pulls message.content from an Ollama /api/chat reply;
  2. make_chat assembles the right payload (model, non-stream, temp 0 + seed) via a mock `post` seam and
     returns the assistant text — proving the request shape without hitting a server;
  3. run_pilot.main drives the whole loop with make_chat monkeypatched to a fooled model -> escape ~1.0,
     writes the curve JSON. (Exercises every live-path line except the socket.)
"""
import json
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, os.path.join(_HERE, "..", "benchmarks", "goodhart"))

import ollama_client as OC      # noqa: E402
import run_pilot as P           # noqa: E402


class TestTransport(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(OC.parse_chat_response({"message": {"content": "hello"}}), "hello")
        self.assertEqual(OC.parse_chat_response({}), "")

    def test_make_chat_payload_and_return(self):
        seen = {}
        def fake_post(url, payload, timeout):
            seen["url"] = url; seen["payload"] = payload
            return {"message": {"content": '{"defect": false}'}}
        chat = OC.make_chat("qwen2.5:7b", host="http://localhost:11434", post=fake_post)
        out = chat("PROMPT")
        self.assertEqual(out, '{"defect": false}')
        self.assertTrue(seen["url"].endswith("/api/chat"))
        self.assertEqual(seen["payload"]["model"], "qwen2.5:7b")
        self.assertFalse(seen["payload"]["stream"])
        self.assertEqual(seen["payload"]["options"]["temperature"], 0.0)
        self.assertEqual(seen["payload"]["messages"][0]["content"], "PROMPT")


class TestPilotRunner(unittest.TestCase):
    def test_pilot_with_fooled_model(self):
        orig = OC.make_chat
        OC.make_chat = lambda *a, **k: (lambda prompt: '{"defect": false}')   # a model fooled every time
        try:
            with tempfile.TemporaryDirectory() as d:
                out = os.path.join(d, "pilot.json")
                P.main(["--model", "mock", "--cell", "defenses_off",
                        "--pressures", "0,4,8", "--k", "5", "--seeds", "2", "--out", out])
                res = json.load(open(out, encoding="utf-8"))
                self.assertEqual(res["curve"]["8"]["mean"], 1.0)   # fooled -> full escape among gold-INVALID
                self.assertEqual(res["seeds"], 2)
        finally:
            OC.make_chat = orig


if __name__ == "__main__":
    unittest.main()
