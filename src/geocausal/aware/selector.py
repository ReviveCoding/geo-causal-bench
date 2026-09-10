"""Pre-treatment-only method-specific gating and risk selection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast

import numpy as np
from sklearn.linear_model import Ridge

FEATURES = (
    "pre_r2",
    "pre_rmse",
    "trend_gap",
    "acf_score",
    "placebo_bias",
    "placebo_fpr",
    "placebo_coverage",
    "donor_hhi",
    "effective_donors",
    "missingness",
    "geo_leverage",
    "method_is_tbr",
    "method_is_did",
    "method_is_ridge_sc",
    "method_is_simplex_sc",
)


@dataclass(frozen=True)
class Selection:
    selected_method: str | None
    abstained: bool
    predicted_risk: float
    eligible_methods: tuple[str, ...]


class AwareSelector:
    def __init__(self, *, risk_limit: float = 1.25) -> None:
        self.risk_limit = risk_limit
        self.model = Ridge(alpha=1.0)
        self._fitted = False

    @staticmethod
    def eligible(method_id: str, features: Mapping[str, float]) -> bool:
        common = (
            features["pre_r2"] >= -0.50
            and features["trend_gap"] <= 0.01
            and features["acf_score"] <= 0.80
            and features["missingness"] <= 0.03
        )
        if not common:
            return False
        if "sc" in method_id:
            return features["donor_hhi"] <= 0.20 and features["effective_donors"] >= 5.0
        return True

    def fit(
        self, feature_rows: Sequence[Mapping[str, float]], losses: np.ndarray
    ) -> None:
        matrix = np.asarray([[row[name] for name in FEATURES] for row in feature_rows])
        self.model.fit(matrix, losses)
        self._fitted = True

    def select(
        self, features_by_method: Mapping[str, Mapping[str, float]]
    ) -> Selection:
        if not self._fitted:
            raise RuntimeError("AWARE selector is not fitted")
        eligible = tuple(
            method
            for method, features in features_by_method.items()
            if self.eligible(method, features)
        )
        if not eligible:
            return Selection(None, True, float("inf"), eligible)
        matrix = np.asarray(
            [[features_by_method[m][name] for name in FEATURES] for m in eligible]
        )
        risks = np.maximum(self.model.predict(matrix), 0)
        best_index = int(np.argmin(risks))
        best_risk = float(risks[best_index])
        if best_risk > self.risk_limit:
            return Selection(None, True, best_risk, eligible)
        return Selection(eligible[best_index], False, best_risk, eligible)

    def export(self) -> dict[str, object]:
        if not self._fitted:
            raise RuntimeError("AWARE selector is not fitted")
        return {
            "architecture": "ridge_risk_model",
            "features": list(FEATURES),
            "coefficient": self.model.coef_.tolist(),
            "intercept": float(self.model.intercept_),
            "alpha": float(self.model.alpha),
            "risk_limit": self.risk_limit,
        }

    @classmethod
    def restore(cls, artifact: Mapping[str, object]) -> AwareSelector:
        selector = cls(risk_limit=float(cast(float, artifact["risk_limit"])))
        selector.model.coef_ = np.asarray(artifact["coefficient"], dtype=float)
        selector.model.intercept_ = float(cast(float, artifact["intercept"]))
        selector.model.n_features_in_ = len(FEATURES)
        selector._fitted = True
        return selector
