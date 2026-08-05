# Self-audit trail for `PAPER_system_description.md`

These are the adversarial audits the paper itself was subjected to, referenced from §9. They are
committed in full — not summarized — because the paper's thesis is that a system built on adversarial
honesty must show the audits that caught it, including the ones that caught a previous fix and the ones
that caught the paper overclaiming.

Unlike the benchmark data (which anonymizes third-party papers behind sealed registers), these carry no
identities to protect: they audit **this engine and this paper**, not anyone's work. No PMCIDs, no DOIs,
nothing sealed. So they ship in the clear.

| file | what it is |
|---|---|
| `round9_audit.ledger.json` | The engine's ledger from the round-9 audit of the paper draft. It upheld four accusations against the engine's own closure guarantees (F-VENDOR, F-HUMAN, F-HOOK, F-SECTIONS), which were then fixed in code. |
| `round10_workorder.md` | The round-10 audit's work order (the human-readable derivative of ledger `audit_round10_paper_v2.ledger.json`). It found a defect *inside* the round-9 fix (B1) plus three honesty debts in the paper, all since corrected, and two residues now declared in §7. |

**Provenance and standing.** Both audits were produced by an Anthropic model — the **same vendor** as
the engine's own roles — so by the engine's own scale they sit at independence level 1–2, **not** a
different nature. They **validate nothing**. Every item in each was re-derived by execution before being
applied; the evidence command is recorded alongside each finding. What neither audit nor the engine can
close — whether the §6 two-frontier result survives a genuinely different-vendor replication — needs an
external human eye and a different vendor, and is stated as such in the paper.
