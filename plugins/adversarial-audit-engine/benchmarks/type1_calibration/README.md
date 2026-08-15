# Type-I (false-demolition) calibration

The engine flags every high-stakes run with the auditor's **Type-I rate** — how often it demolishes a
**valid** artifact. That rate is *measured*, not asserted, by calibrating the auditor on a control
battery. This is option **B**: calibrate the instrument once, then each run **cites** the calibration
(never says "low" — it gives the number and its interval, or "not calibrated").

## Block structure (swappable cards)
The battery is modular. `batteries/` holds one **card** per `battery_id`; `batteries/index.json` names the
single **active** base card. Exactly one card is the base; **domain cards** are added as separate files and
can replace the active base per client/domain. Records are keyed by `(auditor_identity, battery_id)`, so
each card carries its own honest number — swapping the card swaps which battery you calibrate/cite.

- `batteries/general-v2.json` — **active base card**: 24 valid + 12 invalid, VALID-HEAVY and NEAR-MISS.
  The valid items look superficially wrong but survive the strongest defence — that is what actually bounds
  the Type-I rate (a trivially-correct valid item never tempts a false demolition). Numeric/date labels are
  verified in code at build time.
- `batteries/general-v1.json` — original 6+6 card, retained as history (superseded).
- `batteries/index.json` — the manifest: active card + registry + how-to-add-a-domain-card.
- `make_blind.py` — turns any card into a **blind** audit file (neutral, shuffled ids) + a private answer
  key kept out of the repo. Enforces the anti-contamination invariant: the auditor never sees the labels.
- `calibrate.py` — turns an outcomes file into a calibration record (FDR + 95% Wilson CI, TDR, AUC).
- `../../aae/type1_calibration.py` — the math + record store + the `cite()` the run uses.

### Add a domain card
1. Write `batteries/<domain>-v1.json` in the card schema (`id, label, class_hint, artifact, rationale`),
   VALID-HEAVY with near-miss valid items that look wrong but hold.
2. `python3 make_blind.py <domain>-v1 <out_dir> --result-path <path>` → a blind file + a private key.
3. A **fresh, blind** auditor (never one that has seen the labels) scores the blind file.
4. Map neutral→label with the key → `outcomes.json`; then
   `python3 calibrate.py <auditor_identity> outcomes.json _calibration.jsonl <domain>-v1`.
5. If that card should be the base for a client, set it `active` in `index.json`.

## How to calibrate an auditor (BLIND — never show the labels)
1. `python3 make_blind.py general-v2 <out_dir> --result-path <path>` → a blind file (neutral, shuffled
   ids, no labels) + a private key. The auditor must NEVER see the card or the key (anti-contamination).
2. A **fresh** auditor (the same model/agent that runs `/audit`, but with no knowledge of the labels)
   scores the blind file, writing `[{"id":"A01","condemned":true/false,...}, ...]`.
3. Map neutral→label with the private key to get `outcomes.json`
   (`[{"id":"V1","label":"valid","condemned":0}, ...]`), then build the record:
   ```
   python3 calibrate.py "anthropic:claude-<model>" outcomes.json _calibration.jsonl general-v2
   ```
3. Point runs at the store so they cite it:
   ```
   export AAE_CALIBRATION=".../benchmarks/type1_calibration/_calibration.jsonl"
   ```
   Every run for that auditor identity then reports, e.g.
   `TYPE-I: Type-I (false-demolition) = 0% [95% CI 0%-46%, n=6 valid controls], power TDR = 100%, ...`.

## Periodic re-calibration (shipped as a client update)

Calibration is not one-and-done: it is a **periodic safety re-calibration**, delivered to clients as an
update patch. The design supports this natively — records are date-stamped and `latest_calibration()`
returns the most recent, so re-calibrating is just appending a fresh record (and, ideally, shipping a
larger/updated `battery.json`, which tightens the confidence interval). A client update therefore carries
(a) the current battery and (b) the current auditor calibration; runs immediately cite the fresh number.
This also motivates a **staleness guard** (a calibration older than a set window should prompt a re-run)
— a natural next addition.

## Honesty (why the interval matters)
Certainty on a rate scales with the battery size **N**. Six valid controls can only bound the Type-I
loosely (0/6 → 95% CI [0, 0.46]); a tighter bound needs a bigger battery. The record always carries the
Wilson interval, so the run can never present a small-sample estimate as a precise one. Cross-vendor
persistence (the `negation_spectrometry` k-of-m theorem) suppresses spurious demolitions further.
