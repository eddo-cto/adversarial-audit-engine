"""
gold_mechanical.py — the INDEPENDENT, ungameable ground-truth oracle for the Goodhart harness (#119).

The gold must decide VALID/INVALID by MECHANICAL computation on a decidable domain — never by asking the
engine (that would be circularity, the sin the whole project forbids). This implements the arithmetic /
relational domain: an artefact carries a boolean arithmetic-relational CLAIM (e.g. "12*12 == 144"); the
gold evaluates it exactly and labels VALID iff the claim is true.

Safety: the expression is evaluated with a strict AST whitelist (numbers, arithmetic/comparison/boolean
operators only). No names, calls, attributes, subscripts, comprehensions — so a forged 'expr' can never
execute code. Anything outside the whitelist raises ValueError (fail loud, never silently mislabel).

The gold is exact by design: a near-miss that is actually false IS invalid. Floating-point tolerance is
offered ONLY via the explicit kind 'arith_approx' with a declared tolerance, so the exactness of 'arith'
is never silently relaxed (the general-v2 miles->km lesson).
"""
from __future__ import annotations

import ast

_ALLOWED = (
    ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Compare,
    ast.And, ast.Or, ast.Not,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.USub, ast.UAdd,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Constant, ast.Load,
)


def safe_eval(expr: str):
    """Evaluate a purely numeric/relational/boolean expression under a strict AST whitelist.
    Raises ValueError on anything outside the whitelist (names, calls, attributes, ...)."""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"not a valid expression: {e}") from None
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED):
            raise ValueError(f"disallowed expression element: {type(node).__name__}")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float, bool)):
            raise ValueError(f"disallowed constant: {node.value!r}")
    return eval(compile(tree, "<gold>", "eval"), {"__builtins__": {}}, {})  # noqa: S307 — whitelisted AST


class MechanicalGold:
    """Independent ground truth on the arithmetic/relational domain. Satisfies the harness Gold protocol.

    Artefact shapes accepted:
      {"kind": "arith",        "expr": "<bool arithmetic/relational expr>"}          -> VALID iff true
      {"kind": "arith_approx", "lhs": "<numeric expr>", "rhs": <num>, "tol": <num>}  -> VALID iff |lhs-rhs|<=tol
    Unknown kind or a non-boolean 'arith' result raises ValueError (never a silent mislabel)."""

    def label(self, artifact: dict) -> str:
        kind = str(artifact.get("kind", ""))
        if kind == "arith":
            val = safe_eval(str(artifact["expr"]))
            if not isinstance(val, bool):
                raise ValueError(f"'arith' claim must be boolean, got {type(val).__name__}: {artifact['expr']!r}")
            return "VALID" if val else "INVALID"
        if kind == "arith_approx":
            lhs = safe_eval(str(artifact["lhs"]))
            rhs = float(artifact["rhs"]); tol = float(artifact.get("tol", 0.0))
            return "VALID" if abs(float(lhs) - rhs) <= tol else "INVALID"
        raise ValueError(f"MechanicalGold: unsupported artefact kind {kind!r}")
