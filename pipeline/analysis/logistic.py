"""Milestone 10b: exploratory used-available logistic regression.

ROADMAP / ADVANCED, NOT MVP (see REFERENCES.md, M10b). This model
requires independent methodological review before any public claim is
based on it. It exists to sketch the natural next step beyond the
purely descriptive comparison in Milestone 10 — McFadden-Hiller et al.
(2016) use exactly this used-available logistic design on black bear
incident reports — not to produce a publishable finding on its own.

Implemented with plain NumPy IRLS (iteratively reweighted least
squares / Newton-Raphson) rather than a statistics library, so the
exact algorithm is auditable line by line — appropriate for a component
explicitly flagged as needing review, not a black box.

Same caution as everywhere else in this project: a positive association
between "being an observation" and a covariate does not distinguish
observation/reporting bias from real bear habitat selection (see
REFERENCES.md: Sıkdokur et al. 2024, Wilson et al. 2005, McFadden-Hiller
et al. 2016) — a regression coefficient does not resolve this any more
than the descriptive comparison in Milestone 10 does.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

ROADMAP_STATUS = (
    "esplorativo, non MVP: richiede revisione metodologica indipendente prima di "
    "qualunque pubblicazione o affermazione pubblica (vedi REFERENCES.md, M10b)."
)


@dataclass
class LogisticFitResult:
    feature_names: "list[str]"  # includes "intercept" as the first element
    coefficients: "list[float]"
    standard_errors: "list[float]"
    odds_ratios: "list[float]"
    n_used: int
    n_available: int
    n_dropped_missing: int
    n_iterations: int
    converged: bool
    roadmap_status: str = ROADMAP_STATUS


def fit_used_available_logistic(
    used_features: "list[list[float | None]]",
    available_features: "list[list[float | None]]",
    feature_names: "list[str]",
    *,
    max_iterations: int = 50,
    tolerance: float = 1e-8,
) -> LogisticFitResult:
    """`used_features` / `available_features`: rows of covariate values
    for observation ("used") and baseline ("available") points
    respectively, in the same column order as `feature_names`. Rows
    containing any None are dropped entirely — never imputed, since a
    value beyond an OSM/raster search radius is unknown, not zero.

    Covariates are standardized (mean 0, sd 1) before fitting, so
    coefficients/odds-ratios are per-1-standard-deviation, comparable
    across covariates on different raw scales (meters vs. a 0-255
    brightness proxy) — not per-raw-unit.
    """
    n_raw = len(used_features) + len(available_features)
    clean_used = [row for row in used_features if all(v is not None for v in row)]
    clean_available = [row for row in available_features if all(v is not None for v in row)]

    n_used = len(clean_used)
    n_available = len(clean_available)
    n_dropped_missing = n_raw - n_used - n_available

    x = np.array(clean_used + clean_available, dtype=float)
    y = np.array([1.0] * n_used + [0.0] * n_available)

    means = x.mean(axis=0)
    stds = x.std(axis=0)
    stds[stds == 0] = 1.0
    x_std = (x - means) / stds

    design = np.column_stack([np.ones(len(x_std)), x_std])
    n_features = design.shape[1]
    beta = np.zeros(n_features)

    converged = False
    iteration = 0
    for iteration in range(1, max_iterations + 1):
        eta = design @ beta
        p = 1.0 / (1.0 + np.exp(-eta))
        w = np.clip(p * (1 - p), 1e-8, None)
        working_response = eta + (y - p) / w

        xtwx = design.T @ (design * w[:, None])
        xtwz = design.T @ (w * working_response)

        try:
            new_beta = np.linalg.solve(xtwx, xtwz)
        except np.linalg.LinAlgError:
            break

        if np.max(np.abs(new_beta - beta)) < tolerance:
            beta = new_beta
            converged = True
            break
        beta = new_beta

    eta = design @ beta
    p = 1.0 / (1.0 + np.exp(-eta))
    w = np.clip(p * (1 - p), 1e-8, None)
    xtwx_final = design.T @ (design * w[:, None])
    try:
        cov = np.linalg.inv(xtwx_final)
        se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        se = np.full(n_features, float("nan"))

    return LogisticFitResult(
        feature_names=["intercept"] + feature_names,
        coefficients=beta.tolist(),
        standard_errors=se.tolist(),
        odds_ratios=np.exp(beta).tolist(),
        n_used=n_used,
        n_available=n_available,
        n_dropped_missing=n_dropped_missing,
        n_iterations=iteration,
        converged=converged,
    )
