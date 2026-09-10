"""Resumable command-line interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from geocausal.artifacts import canonical_hash, sha256_file
from geocausal.config import ExperimentConfig
from geocausal.simulation.ablations import run_ablations
from geocausal.simulation.benchmark import (
    run_development,
    run_null,
    run_ood_estimator_benchmark,
    run_qualification,
)
from geocausal.simulation.observational import run_observational_benchmark
from geocausal.simulation.protected import (
    create_protected_seed_set,
    evaluate_without_truth,
    prepare_protected_worlds,
    score_committed_once,
)

app = typer.Typer(no_args_is_help=True)


def _root() -> Path:
    return Path.cwd().resolve()


def _receipt_summary(root: Path) -> dict[str, object]:
    """Verify the durable receipt chain and identify the next legal transition."""
    receipt_root = root / "evidence" / "receipts"
    statuses: dict[str, str] = {}
    previous_hash = "ROOT"
    next_transition = "E00"
    for index in range(21):
        phase = f"E{index:02d}"
        path = receipt_root / f"{phase}.json"
        if not path.exists():
            return {
                "receipt_chain_valid": True,
                "phases": statuses,
                "next": phase,
            }
        receipt = json.loads(path.read_text(encoding="utf-8"))
        if receipt.get("phase") != phase:
            raise ValueError(f"Receipt phase mismatch in {path}")
        recorded_previous = receipt.get("input_hashes", {}).get(
            "previous_receipt_or_root"
        )
        if recorded_previous != previous_hash:
            raise ValueError(f"Receipt chain mismatch at {phase}")
        for relative_path, expected_hash in receipt.get("artifacts", {}).items():
            artifact = root / relative_path
            if not artifact.exists() or sha256_file(artifact) != expected_hash:
                raise ValueError(f"Artifact verification failed at {phase}: {artifact}")
        statuses[phase] = str(receipt.get("status", "UNKNOWN"))
        previous_hash = sha256_file(path)
        next_transition = str(receipt.get("next_legal_transition", "UNKNOWN"))

    optional = receipt_root / "E21.json"
    if optional.exists():
        receipt = json.loads(optional.read_text(encoding="utf-8"))
        if receipt.get("input_hashes", {}).get("E20") != previous_hash:
            raise ValueError("Receipt chain mismatch at E21")
        statuses["E21"] = str(receipt.get("status", "UNKNOWN"))
    return {
        "receipt_chain_valid": True,
        "phases": statuses,
        "next": next_transition,
    }


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
def ablations() -> None:
    """Run the post-final E15 ablation family."""
    root = _root()
    freeze = json.loads(
        (root / "artifacts" / "freeze" / "freeze_manifest.json").read_text()
    )
    config = ExperimentConfig.from_yaml(root / "configs" / "frozen" / "experiment.yaml")
    selector = json.loads((root / freeze["selector_artifact"]).read_text())
    typer.echo(
        json.dumps(
            run_ablations(root, config, freeze["protocol_id"], selector), indent=2
        )
    )


@app.command()
def observational() -> None:
    """Run the separately governed E16 staggered-panel benchmark."""
    root = _root()
    freeze = json.loads(
        (root / "artifacts" / "freeze" / "freeze_manifest.json").read_text()
    )
    typer.echo(
        json.dumps(run_observational_benchmark(root, freeze["protocol_id"]), indent=2)
    )


@app.command()
def pipeline(
    resume: Annotated[
        bool, typer.Option("--resume", help="Reuse verified receipts.")
    ] = False,
) -> None:
    """Verify receipts and report the next legal resumable transition."""
    root = _root()
    state: dict[str, object] = {
        "resume": resume,
        "root": str(root),
    }
    state.update(_receipt_summary(root))
    if state["next"] == "AUDIT_COMPLETE":
        state["message"] = "E00-E20 are complete; protected E14 will not rerun."
    typer.echo(json.dumps(state, indent=2))


__all__ = ["app"]
