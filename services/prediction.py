from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DeploymentRiskFeatures:
    deployment_frequency: float
    lead_time: float
    mttr: float
    failure_rate: float
    recent_incidents: int


class DeploymentRiskPredictor:
    """RandomForest-backed predictor with a deterministic fallback for demos."""

    def __init__(self):
        self.model = None
        try:
            from sklearn.ensemble import RandomForestClassifier

            self.model = RandomForestClassifier(n_estimators=80, random_state=42, class_weight="balanced")
        except Exception:
            self.model = None

    def train(self, rows: list[tuple[DeploymentRiskFeatures, int]]) -> None:
        if not self.model or not rows:
            return
        x = [self._vector(features) for features, _ in rows]
        y = [label for _, label in rows]
        self.model.fit(x, y)

    def predict(self, features: DeploymentRiskFeatures) -> dict:
        if self.model is not None and hasattr(self.model, "classes_"):
            risk = float(self.model.predict_proba([self._vector(features)])[0][-1])
        else:
            risk = min(
                1.0,
                (features.failure_rate / 100 * 0.45)
                + min(features.mttr / 120, 1) * 0.25
                + min(features.lead_time / 240, 1) * 0.15
                + min(features.recent_incidents / 10, 1) * 0.15
                - min(features.deployment_frequency / 20, 0.15),
            )
        return {"risk_score": round(max(risk, 0.0), 4), "prediction": "HIGH_RISK" if risk >= 0.7 else "LOW_RISK"}

    @staticmethod
    def _vector(features: DeploymentRiskFeatures) -> list[float]:
        return [
            features.deployment_frequency,
            features.lead_time,
            features.mttr,
            features.failure_rate,
            float(features.recent_incidents),
        ]
