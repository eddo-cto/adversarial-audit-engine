# Type-I (false-demolition) calibration

The engine flags every high-stakes run with the auditor's **Type-I rate** — how often it demolishes a
**valid** artifact. That rate is *measured*, not asserted, by calibrating the auditor on a control
battery. This is option **B**: calibrate the instrument once, then each run **cites** the calibration
(never says "low" — it gives the number and its interval, or "not calibrated").

## Files
- `battery.json` — the control battery: VALID items (must survive) + INVALID items (must die), balanced
  across defect classes. A fallible, domain-neutral yardstick; a domain-specific battery calibrates
  better. Version it (`battery_id`).
- `calibrate.py` — turns an outcomes file into a calibration record (FDR + 95% Wilson CI, TDR, AUC).
- `../../aae/type1_calibration.py` — the math + record store + the `cite()` the run uses.

## How to calibrate an auditor
1. Have the auditor (the same model/agent that runs `/audit`) audit **every** item in `battery.json`,
   and record per item whether it demolished it (`condemned` = asserted a real defect):
   ```json
   [{"id":"V1","label":"valid","condemned":0}, {"id":"I1","label":"invalid","condemned":1}, ...]
   ```
   Save as `outcomes.json`.
2. Build the record:
   ```
   python3 calibrate.py "anthropic:claude-<model>" outcomes.json _calibration.jsonl general-v1
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
