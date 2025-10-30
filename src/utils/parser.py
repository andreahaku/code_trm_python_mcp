"""Output parser utilities for test results and errors."""

import json
import re
from typing import Optional
from ..types import TestResults


def parse_pytest_output(output: str) -> Optional[TestResults]:
    """
    Parse pytest output to extract test results.

    Supports:
    - JSON output (pytest --json)
    - Standard pytest output

    Args:
        output: pytest stdout/stderr

    Returns:
        TestResults or None if parsing failed
    """
    # Try JSON format first (pytest --json or pytest-json-report)
    try:
        data = json.loads(output)
        if "tests" in data:
            # pytest-json-report format
            passed = data.get("passed", 0)
            failed = data.get("failed", 0)
            total = data.get("total", passed + failed)
            return TestResults(passed=passed, failed=failed, total=total, raw=output)
        elif "summary" in data:
            # Other JSON formats
            summary = data["summary"]
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            total = summary.get("total", passed + failed)
            return TestResults(passed=passed, failed=failed, total=total, raw=output)
    except (json.JSONDecodeError, KeyError):
        pass

    # Parse standard pytest output
    # Look for: "X passed", "Y failed" patterns
    passed_match = re.search(r"(\d+) passed", output)
    failed_match = re.search(r"(\d+) failed", output)

    if passed_match or failed_match:
        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        total = passed + failed

        return TestResults(passed=passed, failed=failed, total=total, raw=output)

    # Check for "no tests collected" or "no tests ran"
    if "no tests ran" in output.lower() or "no tests collected" in output.lower():
        return TestResults(passed=0, failed=0, total=0, raw=output)

    # Could not parse
    return None


def parse_unittest_output(output: str) -> Optional[TestResults]:
    """
    Parse unittest output to extract test results.

    Args:
        output: unittest stdout/stderr

    Returns:
        TestResults or None if parsing failed
    """
    # Look for patterns like:
    # "Ran 5 tests in 0.002s"
    # "OK" or "FAILED (failures=2)"

    ran_match = re.search(r"Ran (\d+) test", output)
    if not ran_match:
        return None

    total = int(ran_match.group(1))

    # Check if all passed
    if re.search(r"\\bOK\\b", output):
        return TestResults(passed=total, failed=0, total=total, raw=output)

    # Check for failures
    failed_match = re.search(r"FAILED.*failures?=(\d+)", output)
    if failed_match:
        failed = int(failed_match.group(1))
        passed = total - failed
        return TestResults(passed=passed, failed=failed, total=total, raw=output)

    # Check for errors
    errors_match = re.search(r"errors?=(\d+)", output)
    if errors_match:
        errors = int(errors_match.group(1))
        passed = total - errors
        return TestResults(passed=passed, failed=errors, total=total, raw=output)

    # Unknown format, assume all passed if OK is mentioned
    if "OK" in output:
        return TestResults(passed=total, failed=0, total=total, raw=output)

    return None


def parse_test_output(output: str, framework: str = "pytest") -> Optional[TestResults]:
    """
    Parse test output based on framework.

    Args:
        output: Test command output
        framework: Test framework ("pytest" or "unittest")

    Returns:
        TestResults or None if parsing failed
    """
    if framework == "pytest":
        return parse_pytest_output(output)
    elif framework == "unittest":
        return parse_unittest_output(output)
    else:
        # Try both
        result = parse_pytest_output(output)
        if result is None:
            result = parse_unittest_output(output)
        return result


def parse_performance_metric(output: str) -> Optional[float]:
    """
    Parse performance metric from command output.

    Looks for:
    - Numbers followed by units (ms, s, seconds)
    - JSON output with "time", "duration", "runtime" keys
    - Standalone numbers

    Args:
        output: Performance command output

    Returns:
        Performance value in seconds, or None if not found
    """
    # Try JSON format
    try:
        data = json.loads(output)
        for key in ["time", "duration", "runtime", "elapsed", "seconds"]:
            if key in data:
                value = float(data[key])
                # Assume it's in seconds unless it's very large (milliseconds)
                return value if value < 10000 else value / 1000.0
    except (json.JSONDecodeError, KeyError, ValueError):
        pass

    # Try pattern matching
    # Look for: "123.45 ms", "1.23s", "0.5 seconds"
    patterns = [
        (r"(\d+(?:\.\d+)?)\s*ms", 0.001),  # milliseconds
        (r"(\d+(?:\.\d+)?)\s*s(?:ec(?:ond)?s?)?\\b", 1.0),  # seconds
        (r"(\d+(?:\.\d+)?)\s*m(?:in(?:ute)?s?)?", 60.0),  # minutes
    ]

    for pattern, multiplier in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            return value * multiplier

    # Try standalone number (assume seconds)
    match = re.search(r"^\s*(\d+(?:\.\d+)?)\s*$", output, re.MULTILINE)
    if match:
        return float(match.group(1))

    return None
