"""Evaluation pipeline for running data quality, tests, lint, and performance checks."""

from pathlib import Path
from typing import Optional, Tuple
from ....types import (
    SessionState,
    EvalResult,
    TestResults,
    PerfResults,
)
from ....utils.command import run_command
from ....utils.parser import parse_test_output, parse_performance_metric
from ....utils.scoring import (
    calculate_weighted_score,
    update_ema_score,
    should_halt_iteration,
)


async def run_evaluation(session: SessionState) -> EvalResult:
    """
    Run full evaluation pipeline for current session state.

    Runs (if configured):
    1. Data quality checks
    2. Tests
    3. Lint
    4. Performance benchmark

    Calculates weighted score and updates EMA.

    Args:
        session: Current session state

    Returns:
        EvalResult with scores and feedback
    """
    repo_path = Path(session.cfg.repo_path)
    timeout = session.cfg.timeout_sec

    # Initialize result
    ok_data_quality = None
    ok_lint = None
    tests = None
    perf = None
    feedback = []

    # 1. Run data quality checks
    if session.cfg.data_quality_cmd:
        result = await run_command(
            session.cfg.data_quality_cmd,
            repo_path,
            timeout,
        )
        ok_data_quality = result.ok

        if not result.ok:
            feedback.append(f"❌ Data quality: {result.stderr[:200]}")
        else:
            feedback.append("✅ Data quality passed")

    # 2. Run tests
    if session.cfg.test_cmd:
        result = await run_command(
            session.cfg.test_cmd,
            repo_path,
            timeout,
        )

        # Parse test output
        combined_output = result.stdout + "\\n" + result.stderr
        tests = parse_test_output(combined_output, "pytest")

        if tests:
            if tests.failed > 0:
                feedback.append(
                    f"❌ Tests: {tests.failed}/{tests.total} failed"
                )
            else:
                feedback.append(f"✅ Tests: {tests.passed}/{tests.total} passed")
        else:
            feedback.append("⚠️  Could not parse test output")

    # 3. Run lint
    if session.cfg.lint_cmd:
        result = await run_command(
            session.cfg.lint_cmd,
            repo_path,
            timeout,
        )
        ok_lint = result.ok

        if not result.ok:
            # Extract error count if possible
            stderr_lines = result.stderr.split("\\n")
            error_summary = stderr_lines[-5:] if len(stderr_lines) > 5 else stderr_lines
            feedback.append(f"❌ Lint errors: {'; '.join(error_summary)}")
        else:
            feedback.append("✅ Lint passed")

    # 4. Run performance benchmark
    if session.cfg.perf_cmd:
        result = await run_command(
            session.cfg.perf_cmd,
            repo_path,
            timeout,
        )

        # Parse performance metric
        combined_output = result.stdout + "\\n" + result.stderr
        perf_value = parse_performance_metric(combined_output)

        if perf_value is not None:
            perf = PerfResults(value=perf_value, unit="seconds")

            # Update best performance
            if session.best_perf is None or perf_value < session.best_perf:
                improvement = ""
                if session.best_perf is not None:
                    improvement = f" (↓ {session.best_perf - perf_value:.3f}s)"
                    session.best_perf = perf_value
                feedback.append(f"⚡ Performance: {perf_value:.3f}s{improvement}")
            else:
                regression = perf_value - session.best_perf
                feedback.append(f"⚠️  Performance: {perf_value:.3f}s (↑ {regression:.3f}s)")
        else:
            feedback.append("⚠️  Could not parse performance metric")

    # Calculate weighted score
    score = calculate_weighted_score(
        ok_data_quality=ok_data_quality,
        ok_lint=ok_lint,
        tests=tests,
        perf=perf,
        weights=session.cfg.weights,
        best_perf=session.best_perf,
    )

    # Update EMA score
    ema_score = update_ema_score(
        current_score=score,
        prev_ema=session.ema_score if session.step > 0 else score,
        alpha=session.ema_alpha,
    )

    # Increment step
    new_step = session.step + 1

    # Update improvement streak
    no_improve_streak = session.no_improve_streak
    if score > session.best_score:
        no_improve_streak = 0
        session.best_score = score
    else:
        no_improve_streak += 1

    # Check halting condition
    tests_passed = tests is not None and tests.failed == 0 if tests else False
    should_halt, halt_reasons = should_halt_iteration(
        step=new_step,
        score=score,
        ema_score=ema_score,
        no_improve_streak=no_improve_streak,
        tests_passed=tests_passed,
        max_steps=session.cfg.halt.max_steps,
        pass_threshold=session.cfg.halt.pass_threshold,
        patience_no_improve=session.cfg.halt.patience_no_improve,
        min_steps=session.cfg.halt.min_steps,
    )

    # Create evaluation result
    eval_result = EvalResult(
        ok_data_quality=ok_data_quality,
        ok_lint=ok_lint,
        tests=tests,
        perf=perf,
        score=score,
        ema_score=ema_score,
        step=new_step,
        feedback=feedback,
        should_halt=should_halt,
        reasons=halt_reasons,
    )

    # Update session state
    session.step = new_step
    session.ema_score = ema_score
    session.no_improve_streak = no_improve_streak
    session.history.append(eval_result)

    return eval_result


async def run_preflight_checks(session: SessionState) -> dict:
    """
    Run preflight validation checks before starting iteration.

    Checks:
    - Repository exists
    - Commands are available
    - Initial build/test pass

    Args:
        session: Session state

    Returns:
        Preflight results dictionary
    """
    repo_path = Path(session.cfg.repo_path)
    results = {
        "repoExists": repo_path.exists() and repo_path.is_dir(),
        "commandsAvailable": {},
        "initialBuild": None,
        "initialTests": None,
    }

    if not results["repoExists"]:
        return results

    # Check command availability
    from ....utils.command import check_command_available

    if session.cfg.data_quality_cmd:
        cmd_name = session.cfg.data_quality_cmd.split()[0]
        results["commandsAvailable"]["dataQuality"] = check_command_available(cmd_name)

    if session.cfg.test_cmd:
        cmd_name = session.cfg.test_cmd.split()[0]
        results["commandsAvailable"]["test"] = check_command_available(cmd_name)

    if session.cfg.lint_cmd:
        cmd_name = session.cfg.lint_cmd.split()[0]
        results["commandsAvailable"]["lint"] = check_command_available(cmd_name)

    # Run initial build (data quality check)
    if session.cfg.data_quality_cmd:
        result = await run_command(
            session.cfg.data_quality_cmd,
            repo_path,
            session.cfg.timeout_sec,
        )
        results["initialBuild"] = {
            "success": result.ok,
            "output": result.stdout[:500] if result.ok else result.stderr[:500],
        }

    # Run initial tests
    if session.cfg.test_cmd:
        result = await run_command(
            session.cfg.test_cmd,
            repo_path,
            session.cfg.timeout_sec,
        )
        combined = result.stdout + "\\n" + result.stderr
        tests = parse_test_output(combined, "pytest")

        results["initialTests"] = {
            "success": result.ok and (tests.failed == 0 if tests else False),
            "passed": tests.passed if tests else 0,
            "failed": tests.failed if tests else 0,
            "total": tests.total if tests else 0,
        }

    return results
