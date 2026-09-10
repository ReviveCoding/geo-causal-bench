"""Validated benchmark configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class WorldBudgets(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    smoke: int = Field(ge=10)
    pilot: int = Field(ge=20)
    development: int = Field(ge=50)
    qualification: int = Field(ge=100)
    null_calibration: int = Field(ge=1000, le=2000)
    final: int = Field(ge=500, le=2000)


class ExperimentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    protocol_stage: Literal["development", "qualification", "frozen"]
    seed: int
    n_geos: int = Field(ge=10)
    pre_days: int = Field(ge=84)
    test_days: int = Field(ge=14)
    cooldown_days: int = Field(ge=0)
    treatment_share: float = Field(gt=0, lt=0.5)
    alpha: float = Field(gt=0, lt=0.5)
    target_power: float = Field(gt=0.5, lt=1)
    kpi: Literal["conversions"]
    experiment_type: Literal["heavy_up", "holdback", "go_dark"]
    assignment: Literal["random", "stratified"]
    worlds: WorldBudgets

    @classmethod
    def from_yaml(cls, path: Path) -> ExperimentConfig:
        return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
