from __future__ import annotations

from pipeline.analysis.logistic import fit_used_available_logistic

# Deterministic synthetic data (not random — tests must not be flaky):
# "used" points have a systematically higher mean than "available"
# points, but the two groups overlap (e.g. "used" includes a 1, matched
# by an "available" 3) — perfectly separated groups make the logistic
# MLE diverge (see the dedicated non-convergence test below), so a
# realistic positive-effect fixture needs overlap to converge at all.
SEPARATED_USED = [[3.0], [4.0], [5.0], [2.0], [3.0], [4.0], [1.0], [3.0]]
SEPARATED_AVAILABLE = [[0.0], [1.0], [-1.0], [2.0], [0.0], [1.0], [-1.0], [3.0]]

# Same distribution in both groups: no real relationship expected.
NO_EFFECT_USED = [[0.0], [1.0], [-1.0], [0.5], [-0.5], [1.0], [0.0], [-1.0]]
NO_EFFECT_AVAILABLE = [[0.0], [1.0], [-1.0], [0.5], [-0.5], [1.0], [0.0], [-1.0]]


def test_positive_association_is_detected_with_correct_sign():
    result = fit_used_available_logistic(SEPARATED_USED, SEPARATED_AVAILABLE, ["covariate"])

    covariate_coef = result.coefficients[1]
    covariate_se = result.standard_errors[1]

    assert result.converged
    assert covariate_coef > 0
    assert abs(covariate_coef / covariate_se) > 2  # roughly "significant"
    assert result.odds_ratios[1] > 1


def test_no_association_gives_small_coefficient():
    result = fit_used_available_logistic(NO_EFFECT_USED, NO_EFFECT_AVAILABLE, ["covariate"])

    covariate_coef = result.coefficients[1]

    assert result.converged
    assert abs(covariate_coef) < 0.5


def test_rows_with_missing_values_are_dropped_not_imputed():
    used = [[1.0], [None], [2.0]]
    available = [[0.0], [0.0], [None]]

    result = fit_used_available_logistic(used, available, ["covariate"])

    assert result.n_used == 2
    assert result.n_available == 2
    assert result.n_dropped_missing == 2


def test_feature_names_are_prefixed_with_intercept():
    result = fit_used_available_logistic(SEPARATED_USED, SEPARATED_AVAILABLE, ["night_light_proxy"])
    assert result.feature_names == ["intercept", "night_light_proxy"]
    assert len(result.coefficients) == 2


def test_result_always_carries_the_roadmap_status_caveat():
    result = fit_used_available_logistic(SEPARATED_USED, SEPARATED_AVAILABLE, ["covariate"])
    assert "non MVP" in result.roadmap_status
    assert "revisione" in result.roadmap_status


def test_perfectly_separable_groups_do_not_converge():
    # No overlap at all between groups: the logistic MLE has no finite
    # solution (the coefficient diverges towards infinity) — this must
    # surface as converged=False, not a silently huge/meaningless number
    # presented as if it were a normal estimate.
    perfectly_used = [[3.0], [4.0], [5.0], [3.5], [4.5], [5.5], [3.0], [4.0]]
    perfectly_available = [[0.0], [1.0], [-1.0], [0.5], [-0.5], [1.0], [0.0], [-1.0]]

    result = fit_used_available_logistic(perfectly_used, perfectly_available, ["covariate"])

    assert result.converged is False
