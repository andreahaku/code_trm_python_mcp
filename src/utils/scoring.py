"""Scoring utilities for TRM evaluation."""

from typing import Optional
from ..types import WeightsConfig, TestResults, PerfResults


def calculate_weighted_score(
    ok_data_quality: Optional[bool],
    ok_lint: Optional[bool],
    tests: Optional[TestResults],
    perf: Optional[PerfResults],
    weights: WeightsConfig,
    best_perf: Optional[float] = None,
) -> float:
    """
    Calculate weighted score from evaluation signals.

    Score is in [0, 1] range.

    Args:
        ok_data_quality: Whether data quality checks passed
        ok_lint: Whether lint checks passed
        tests: Test results
        perf: Performance metrics
        weights: Weight configuration
        best_perf: Best performance value seen so far (lower is better)

    Returns:
        Weighted score in [0, 1]
    """
    components = []
    total_weight = 0.0

    # Data quality signal
    if ok_data_quality is not None:
        s_data_quality = 1.0 if ok_data_quality else 0.0
        components.append(weights.data_quality * s_data_quality)
        total_weight += weights.data_quality

    # Test signal
    if tests is not None and tests.total > 0:
        s_tests = tests.passed / tests.total
        components.append(weights.test * s_tests)
        total_weight += weights.test

    # Lint signal
    if ok_lint is not None:
        s_lint = 1.0 if ok_lint else 0.0
        components.append(weights.lint * s_lint)
        total_weight += weights.lint

    # Performance signal (normalized: best/current, lower runtime is better)
    if perf is not None and perf.value > 0:
        if best_perf is not None and best_perf > 0:
            # Normalize: best/current (capped at 1.0)
            s_perf = min(1.0, best_perf / perf.value)
        else:
            # First measurement, assume baseline
            s_perf = 1.0
        components.append(weights.perf * s_perf)
        total_weight += weights.perf

    # Calculate weighted average
    if total_weight == 0:
        return 0.0

    return sum(components) / total_weight


def update_ema_score(
    current_score: float,
    prev_ema: float,
    alpha: float
) -> float:
    """
    Update EMA (Exponential Moving Average) score.

    EMA = alpha * current + (1 - alpha) * previous_ema

    Args:
        current_score: Current iteration score
        prev_ema: Previous EMA value
        alpha: Smoothing factor (0 to 1, higher = more weight on current)

    Returns:
        Updated EMA score
    """
    return alpha * current_score + (1 - alpha) * prev_ema


def should_halt_iteration(
    step: int,
    score: float,
    ema_score: float,
    no_improve_streak: int,
    tests_passed: bool,
    max_steps: int,
    pass_threshold: float,
    patience_no_improve: int,
    min_steps: int = 1,
) -> tuple[bool, list[str]]:
    """
    Determine if iteration should halt based on halting policy.

    Halting conditions:
    1. Success: step >= min_steps AND all tests pass AND score >= pass_threshold
    2. Plateau: No improvement for patience_no_improve consecutive steps
    3. Limit: Reached max_steps

    Args:
        step: Current iteration step
        score: Current score
        ema_score: EMA score
        no_improve_streak: Number of steps without improvement
        tests_passed: Whether all tests are passing
        max_steps: Maximum allowed steps
        pass_threshold: Score threshold for success
        patience_no_improve: Steps without improvement before halting
        min_steps: Minimum steps before allowing success halt

    Returns:
        Tuple of (should_halt, reasons)
    """
    reasons = []

    # Condition 1: Success
    if step >= min_steps and tests_passed and score >= pass_threshold:
        reasons.append(
            f"✅ Success: Tests passing and score {score:.3f} >= threshold {pass_threshold}"
        )
        return True, reasons

    # Condition 2: Plateau (no improvement)
    if no_improve_streak >= patience_no_improve:
        reasons.append(
            f"⏸️  Plateau: No improvement for {no_improve_streak} steps (patience={patience_no_improve})"
        )
        return True, reasons

    # Condition 3: Max steps reached
    if step >= max_steps:
        reasons.append(f"⏱️  Limit: Reached max steps ({max_steps})")
        return True, reasons

    # Continue iterating
    reasons.append(f"🔄 Continue: Step {step}/{max_steps}, score={score:.3f}, ema={ema_score:.3f}")
    return False, reasons
