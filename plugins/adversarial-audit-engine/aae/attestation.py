"""
attestation.py — make the closure guarantees real, not conventions.

Round 11 (after the first different-vendor / level-3 review). Two closure claims
that round 10 could only *declare* as residue are now enforced in code:

  * HUMAN CLOSURE is cryptographic. VALIDATED requires an HMAC the model cannot
    forge: token == HMAC(operator_key, content_digest(ledger)). The operator key
    lives outside the model's reach (env AAE_HUMAN_KEY, or a file); the model
    authors the payload but not the key, so it cannot produce the token. A bare,
    unverifiable string no longer validates anything.

  * VENDOR INDEPENDENCE is attested, not claimed. Level 3 is credited only when
    the reviewer identity is confirmed by the adapter that actually made the call
    (env AAE_EXTERNAL_ATTESTED_IDENTITY), not by a string the model wrote into the
    payload. An unattested different-vendor claim is marked CLAIMED and its
    independence is not credited.

Pure standard library (hashlib, hmac). No third-party crypto.
"""
from __future__ import annotations

import hashlib
import hmac
import json


def content_digest(artifact_name: str, findings) -> str:
    """Stable SHA-256 over the substance a human actually reviews: the artifact
    name and, per finding, its element and adjudicated verdict. Volatile fields
    (timestamps, completion_state, flags) are excluded so the digest is identical
    whether recomputed from the live Ledger (run_core) or the persisted JSON
    (the Stop hook). `findings` is any iterable of mappings with 'element' and
    'verdict' keys (verdict already reduced to its string value)."""
    norm = [
        {"element": str(f.get("element", "")), "verdict": str(f.get("verdict", ""))}
        for f in findings
    ]
    blob = json.dumps({"artifact_name": str(artifact_name), "findings": norm},
                      sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def make_human_token(digest: str, key: str) -> str:
    """Convenience for the operator (and tests): the token to set as
    AAE_HUMAN_ATTESTATION after reviewing an artifact whose digest is `digest`."""
    return hmac.new(key.encode("utf-8"), digest.encode("utf-8"),
                    hashlib.sha256).hexdigest()


def verify_human_attestation(digest: str, token: str | None, key: str | None) -> bool:
    """True iff `token` is a valid HMAC of `digest` under `key`. Constant-time.
    Missing key or token → False (an unverifiable assertion is not closure)."""
    if not token or not key:
        return False
    expected = make_human_token(digest, key)
    return hmac.compare_digest(expected, token.strip())
