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
| `round10_workorder.md` | The round-10 audit's work order (the human-readable derivative of ledger `audit_round10_paper_v2.ledger.json`). It found a defect *inside* the round-9 fix (B1) plus three honesty debts in the paper, all since corrected, and two residues declared in §7. |
| `round11_review_level3.md` | The **first different-vendor (level-3)** review. It reproduced the four guards, then forced §6 down to a *descriptive dissociation* and confirmed the two closure residues were still conventions — which round 11 then built in code (HMAC human closure; adapter-attested vendor level). |

**Provenance and standing.** The round-9 and round-10 audits were produced by an Anthropic model — the
**same vendor** as the engine's own roles — so by the engine's own scale they sit at independence level
1–2. The round-11 review was produced by a **different vendor**: independence **level 3**, the axis §7
says the system cannot supply for itself. None of them **validate anything** — closure remains a human's.
Every applied item was re-derived by execution first. The level-3 review is what forced §6 from "two
orthogonal frontiers" down to a descriptive dissociation, and confirmed the two closure guarantees were
still conventions (built in code in round 11). What remains open — whether the §6 dissociation survives a
*further* genuinely different-vendor **replication of the experiment** (not just a review), and whether
the mechanism taxonomy carves the space — still needs an external human eye and another vendor.
