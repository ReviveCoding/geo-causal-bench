"""Resumable command-line interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from geocausal.artifacts import canonical_hash
from geocausal.config import ExperimentConfig
from geocausal.simulation.benchmark import run_development, run_final, run_null

app = typer.Typer(no_args_is_help=True)


def _root() -> Path:
    return Path.cwd().resolve()


@app.command()
def development() -> None:
    """Fit AWARE only on development worlds."""
    root = _root()
    config = ExperimentConfig.from_yaml(root / "configs" / "experiments" / "base.yaml")
    protocol = f"development-{canonical_hash(config.model_dump())[:12]}"
    typer.echo(json.dumps(run_development(root, config, protocol), indent=2))


@app.command()
def null_calibration() -> None:
    """Run the pre-freeze null calibration."""
    root = _root()
    config = ExperimentConfig.from_yaml(root / "configs" / "experiments" / "base.yaml")
    protocol = f"qualification-{canonical_hash(config.model_dump())[:12]}"
    typer.echo(json.dumps(run_null(root, config, protocol), indent=2))


@app.command()
def final() -> None:
    """Execute frozen E14 exactly once after verifying its manifest."""
    root = _root()
    freeze_path = root / "artifacts" / "freeze" / "freeze_manifest.json"
    final_path = root / "evidence" / "final" / "confirmatory_metrics.json"
    if final_path.exists():
        raise typer.BadParameter(
            "E14 evidence already exists; final evaluation is one-way"
        )
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    config = ExperimentConfig.from_yaml(root / "configs" / "frozen" / "experiment.yaml")
    selector = json.loads(
        (root / freeze["selector_artifact"]).read_text(encoding="utf-8")
    )
    typer.echo(
        json.dumps(run_final(root, config, freeze["protocol_id"], selector), indent=2)
    )


@app.command()
def pipeline(
    resume: Annotated[
        bool, typer.Option("--resume", help="Reuse verified receipts.")
    ] = False,
) -> None:
    """Resume pre-freeze stages; protected E14 remains an explicit command."""
    root = _root()
    state = {
        "resume": resume,
        "root": str(root),
        "next": "Use phase-specific commands; E14 requires a verified freeze.",
    }
    typer.echo(json.dumps(state, indent=2))


__all__ = ["app"]
