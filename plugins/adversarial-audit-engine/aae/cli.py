"""
cli.py — Command-line entry point.

Usage:
    python -m aae.cli AUDIT path/to/artifact.md [--domain "..."] \
        [--backend mock|anthropic] [--model claude-sonnet-4-6] \
        [--posta low|medium|high] [--external-id NAME] [--out OUTDIR]

With --backend mock (default) it runs fully offline — good for a smoke test.
With --backend anthropic it uses the real model (needs ANTHROPIC_API_KEY).
"""

from __future__ import annotations

import argparse
import sys

from .config import AuditConfig
from .llm import MockLLMClient, AnthropicLLMClient
from .orchestrator import Orchestrator, write_outputs
from .schema import Posta


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="aae", description="Adversarial Audit Engine")
    p.add_argument("command", choices=["AUDIT"], help="what to do")
    p.add_argument("artifact", help="path to the artifact file to audit")
    p.add_argument("--domain", default="", help="optional domain hint")
    p.add_argument("--backend", default="mock", choices=["mock", "anthropic"])
    p.add_argument("--model", default="claude-sonnet-4-6")
    p.add_argument("--posta", default="high", choices=["low", "medium", "high"])
    p.add_argument("--external-id", default=None,
                   help="identity of an external reviewer, if one ran")
    p.add_argument("--out", default="./aae_out")
    args = p.parse_args(argv)

    try:
        with open(args.artifact, "r", encoding="utf-8") as fh:
            artifact = fh.read()
    except OSError as e:
        print(f"error: cannot read artifact: {e}", file=sys.stderr)
        return 2

    client = (MockLLMClient() if args.backend == "mock"
              else AnthropicLLMClient(model=args.model))

    config = AuditConfig(
        artifact_path=args.artifact,
        domain_hint=args.domain,
        max_posta=Posta(args.posta),
        external_review_identity=args.external_id,
        out_dir=args.out,
    )

    orch = Orchestrator(client)
    result = orch.run(artifact, config, artifact_name=args.artifact)

    print(result.summary())
    stem = args.artifact.replace("/", "_").replace("\\", "_")
    paths = write_outputs(result, args.out, stem)
    print("\nwritten:")
    for pth in paths:
        print(f"  {pth}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
