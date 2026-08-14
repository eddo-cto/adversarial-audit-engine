"""type1_calibration.py — measure an auditor's Type-I (false-demolition) rate on a control battery,
and report it WITH its uncertainty. This is an error theory, so the estimate is never a bare point:
it carries a Wilson confidence interval, because with a small battery the rate is intrinsically
uncertain and that must be shown, not hidden.

Design (option B, calibration): the auditor is calibrated once on a battery of VALID items (must
survive) and INVALID items (must die); each real run then CITES the calibrated rate. Feeds the existing
`negation_spectrometry.calibrate` (FDR / TDR / AUC); this module adds the confidence interval, the
per-run record, and the read-back used to cite it.

Honesty: certainty on a rate scales with the battery size N. Six valid items can only bound the Type-I
loosely (e.g. 0/6 demolished => 95% CI [0, 0.46]); a tighter bound needs a bigger battery. The CI makes
this explicit on every record. Stdlib only.
"""
from __future__ import annotations

import datetime
import json
import math
import os

from .negation_spectrometry import calibrate as _spectrum

# A control item is "demolished" if the auditor condemned it — a real defect asserted.
CONDEMNING = {"accusa_vince", "accusa_ridimensionata"}


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion k/n. Well-behaved at k=0 and k=n and for
    small n (unlike the normal approximation), which is exactly the regime a control battery lives in."""
    if n <= 0:
        return (0.0, 1.0)
    p = k / n
    d = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = (z / d) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, centre - half), min(1.0, centre + half))


def score_battery(audit_fn, items: list) -> list:
    """Run the auditor over the battery. `audit_fn(artifact_text) -> truthy` iff the auditor DEMOLISHED
    the item (asserted a real defect). Returns per-item outcomes with the ground-truth label."""
    out = []
    for it in items:
        condemned = 1 if bool(audit_fn(it["artifact"])) else 0
        out.append({"id": it["id"], "label": it["label"], "condemned": condemned})
    return out


def calibrate(outcomes: list) -> dict:
    """FDR (Type-I) and TDR (power) with 95% Wilson intervals, plus AUC. `outcomes` is a list of
    {label: 'valid'|'invalid', condemned: 0|1}."""
    sv = [int(o["condemned"]) for o in outcomes if o["label"] == "valid"]
    si = [int(o["condemned"]) for o in outcomes if o["label"] == "invalid"]
    spec = _spectrum(sv, si, threshold=0.5)     # FDR, TDR, AUC (existing, audited math)
    kf, nf = sum(sv), len(sv)
    kt, nt = sum(si), len(si)
    return {
        "n_valid": nf, "false_demolitions": kf,
        "FDR": spec["FDR"], "FDR_ci95": list(wilson_ci(kf, nf)),
        "n_invalid": nt, "true_demolitions": kt,
        "TDR": spec["TDR"], "TDR_ci95": list(wilson_ci(kt, nt)),
        "AUC": spec["AUC"],
    }


def make_record(auditor_identity: str, battery_id: str, outcomes: list) -> dict:
    rec = calibrate(outcomes)
    rec.update({
        "auditor_identity": auditor_identity,
        "battery_id": battery_id,
        "date": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "outcomes": outcomes,
    })
    return rec


def append_calibration(record: dict, store_path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(store_path)), exist_ok=True)
    with open(store_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def latest_calibration(auditor_identity: str, store_path: str) -> dict | None:
    """Most recent calibration for this auditor identity, or None if never calibrated. Used by the
    run to CITE the Type-I; absence means the run honestly reports 'not calibrated', never 'low'."""
    if not os.path.exists(store_path):
        return None
    best = None
    with open(store_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("auditor_identity") == auditor_identity:
                if best is None or r.get("date", "") >= best.get("date", ""):
                    best = r
    return best


def cite(record: dict | None) -> str:
    """One honest line for the ledger/summary. Never 'low' — always the number and its interval."""
    if not record:
        return ("Type-I (false-demolition) NOT CALIBRATED for this auditor: the false-positive rate is "
                "asserted, not measured. Run the control battery to calibrate.")
    lo, hi = record.get("FDR_ci95", [0.0, 1.0])
    return (f"Type-I (false-demolition) = {record['FDR']:.0%} "
            f"[95% CI {lo:.0%}-{hi:.0%}, n={record['n_valid']} valid controls], "
            f"power TDR = {record['TDR']:.0%}, battery '{record.get('battery_id','?')}', "
            f"calibrated {record.get('date','?')[:10]}. Certainty scales with battery size.")
