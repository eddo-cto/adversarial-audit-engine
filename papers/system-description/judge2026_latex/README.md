# JUDGe @ NeurIPS 2026 — LaTeX submission (short paper, double-blind)

Files:
- `judge2026_trust_protocol.tex` — the paper source (anonymized).
- `neurips_2026.sty` — a **faithful stand-in** so it compiles now. **For the real submission, replace it
  with the OFFICIAL `neurips_2026.sty`** from the NeurIPS 2026 template (linked on the JUDGe CFP,
  https://judge2026.github.io/). The `.tex` needs no changes — same filename.
- `judge2026_trust_protocol.pdf` — compiled preview (3 pages; short-paper limit is 4 + references).

Build:
```bash
pdflatex judge2026_trust_protocol.tex
pdflatex judge2026_trust_protocol.tex   # second pass resolves citations
```

Pre-submission checklist:
- [ ] Swap in the official `neurips_2026.sty` (adds line numbers + exact NeurIPS metrics).
- [ ] Keep it anonymous (no name, no repo URL) until acceptance.
- [ ] Upload on OpenReview: https://openreview.net/group?id=NeurIPS.cc/2026/Workshop/JUDGe
- [ ] Deadline: 29 August 2026 (AoE).
- [ ] On acceptance, de-anonymize: author, affiliation, and the artifact repository URL.
