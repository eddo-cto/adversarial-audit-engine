"""
test_bundle_sources.py — folding many documents into one audit artifact (round 22).

Pins:
  1. the bundle names each document with a stable id and lists those ids as evidence_base,
     both in a machine-readable comment and returned to the caller;
  2. duplicate ids are disambiguated (no silent collision);
  3. every document's text is present VERBATIM inside its delimited section (so a quote in
     accusation.evidence stays a verbatim substring of source_text — the grounding gate holds);
  4. the CLI writes the artifact and reads .txt/.md from disk.
"""
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "scripts"))

import bundle_sources as bs  # noqa: E402


class TestMakeBundle(unittest.TestCase):
    def test_manifest_ids_and_evidence_base(self):
        md, ids = bs.make_bundle([
            ("bilancio 2025", "bil.pdf", "Totale attivo 2.888.169"),
            ("visura 2026", "vis.pdf", "conferimento 29/05/2024 ALI.GA"),
        ])
        self.assertEqual(ids, ["bilancio_2025", "visura_2026"])
        self.assertIn("<!-- evidence_base: bilancio_2025, visura_2026 -->", md)
        self.assertIn("| `bilancio_2025` |", md)

    def test_text_is_verbatim_inside_sections(self):
        q = "esigibili oltre l'esercizio successivo 1.587.309"
        md, _ = bs.make_bundle([("bilancio", "b.txt", f"...\n{q}\n...")])
        self.assertIn(q, md)                      # grounding gate will still find the quote
        self.assertIn("INIZIO DOCUMENTO [bilancio]", md)
        self.assertIn("FINE DOCUMENTO [bilancio]", md)

    def test_bundle_emits_stable_artifact_id(self):
        md1, _ = bs.make_bundle([("bilancio 2025", "b.pdf", "X"), ("visura 2026", "v.pdf", "Y")])
        md2, _ = bs.make_bundle([("visura 2026", "v.pdf", "Y2"), ("bilancio 2025", "b.pdf", "X2")])
        # same set of document ids -> same artifact_id regardless of order or text
        import re
        aid = lambda m: re.search(r"artifact_id: (\S+)", m).group(1)
        self.assertEqual(aid(md1), aid(md2))
        self.assertEqual(aid(md1), "bundle:bilancio_2025+visura_2026")

    def test_duplicate_ids_disambiguated(self):
        _, ids = bs.make_bundle([("doc", "a.txt", "x"), ("doc", "b.txt", "y")])
        self.assertEqual(ids, ["doc", "doc_2"])

    def test_sanitize_id(self):
        self.assertEqual(bs._sanitize_id("Bilancio 31/12/2025"), "bilancio_31_12_2025")
        self.assertEqual(bs._sanitize_id("!!!"), "doc")


class TestExtractAndCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _w(self, name, text):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p

    def test_extract_text_file(self):
        p = self._w("a.md", "# titolo\ncorpo")
        self.assertEqual(bs.extract_text(p), "# titolo\ncorpo")

    def test_cli_writes_bundle(self):
        a = self._w("uno.txt", "prezzo 250000")
        b = self._w("due.txt", "condizione sospensiva mutuo 200000")
        out = os.path.join(self.tmp, "audit_input.md")
        rc = bs.main(["-o", out, a, b])
        self.assertEqual(rc, 0)
        content = open(out, encoding="utf-8").read()
        self.assertIn("prezzo 250000", content)
        self.assertIn("condizione sospensiva mutuo 200000", content)
        self.assertIn("evidence_base: uno, due", content)

    def test_cli_explicit_ids(self):
        a = self._w("x.txt", "A")
        b = self._w("y.txt", "B")
        out = os.path.join(self.tmp, "o.md")
        bs.main(["-o", out, "--id", "bilancio_2025=" + a, "--id", "visura_2026=" + b])
        content = open(out, encoding="utf-8").read()
        self.assertIn("evidence_base: bilancio_2025, visura_2026", content)


if __name__ == "__main__":
    unittest.main()
