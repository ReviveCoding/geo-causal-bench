"""Resumable command-line interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from geocausal.artifacts import canonical_hash
from geocausal.config import ExperimentConfig
from geocausal.simulation.benchmark import (
    run_development,
    run_null,
    run_ood_estimator_benchmark,
    run_qualification,
)
from geocausal.simulation.protected import (
    create_protected_seed_set,
    evaluate_without_truth,
    prepare_protected_worlds,
    score_committed_once,
)

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
def qualification() -> None:
    """Run pre-freeze end-to-end AWARE qualification worlds."""
    root = _root()
    config = ExperimentConfig.from_yaml(root / "configs" / "experiments" / "base.yaml")
    artifact = json.loads(
        (root / "artifacts" / "aware" / "selector_development.json").read_text(
            encoding="utf-8"
        )
    )
    protocol = f"qualification-{canonical_hash(config.model_dump())[:12]}"
    typer.echo(
        json.dumps(run_qualification(root, config, protocol, artifact), indent=2)
    )


@app.command()
def ood() -> None:
    """Run estimator-only compound S13 evidence excluded from AWARE fitting."""
    root = _root()
    config = ExperimentConfig.from_yaml(root / "configs" / "experiments" / "base.yaml")
    protocol = f"qualification-{canonical_hash(config.model_dump())[:12]}"
    typer.echo(
        json.dumps(run_ood_estimator_benchmark(root, config, protocol), indent=2)
    )


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
    prepare_protected_worlds(root, config, freeze["protocol_id"])
    evaluate_without_truth(root, config, freeze["protocol_id"], selector)
    typer.echo(
        json.dumps(score_committed_once(root, config, freeze["protocol_id"]), indent=2)
    )


@app.command()
def protect_seeds() -> None:
    """Create a one-time protected final seed set for binding at E13."""
    root = _root()
    config = ExperimentConfig.from_yaml(root / "configs" / "experiments" / "base.yaml")
    typer.echo(json.dumps(create_protected_seed_set(root, config), indent=2))


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
