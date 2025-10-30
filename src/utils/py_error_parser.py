"""Python error and traceback parser."""

import re
from typing import List, Dict, Optional


class PythonError:
    """Parsed Python error information."""

    def __init__(
        self,
        error_type: str,
        message: str,
        file: Optional[str] = None,
        line: Optional[int] = None,
        code_snippet: Optional[str] = None,
        full_traceback: Optional[str] = None,
    ):
        self.error_type = error_type
        self.message = message
        self.file = file
        self.line = line
        self.code_snippet = code_snippet
        self.full_traceback = full_traceback

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "errorType": self.error_type,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "codeSnippet": self.code_snippet,
            "fullTraceback": self.full_traceback,
        }

    def __repr__(self) -> str:
        location = f"{self.file}:{self.line}" if self.file and self.line else "unknown"
        return f"{self.error_type} at {location}: {self.message}"


def parse_python_traceback(stderr: str) -> List[PythonError]:
    """
    Parse Python tracebacks from stderr output.

    Handles:
    - Standard Python tracebacks
    - Syntax errors
    - Import errors
    - Type errors
    - Runtime errors

    Args:
        stderr: Standard error output containing tracebacks

    Returns:
        List of parsed Python errors
    """
    errors = []

    # Split into potential error blocks (separated by "Traceback" or standalone error lines)
    error_blocks = re.split(r"(?=Traceback \\(most recent call last\\):)", stderr)

    for block in error_blocks:
        if not block.strip():
            continue

        # Try to parse as full traceback
        error = _parse_traceback_block(block)
        if error:
            errors.append(error)
            continue

        # Try to parse as standalone error line (e.g., from linters)
        standalone_errors = _parse_standalone_errors(block)
        errors.extend(standalone_errors)

    return errors


def _parse_traceback_block(block: str) -> Optional[PythonError]:
    """Parse a single traceback block."""
    if "Traceback (most recent call last):" not in block:
        return None

    lines = block.strip().split("\n")

    # Find the error type and message (usually the last line)
    error_line = lines[-1] if lines else ""
    error_match = re.match(r"(\w+(?:Error|Exception|Warning)):\s*(.*)", error_line)

    if not error_match:
        return None

    error_type = error_match.group(1)
    message = error_match.group(2)

    # Find file and line number from traceback
    file_path = None
    line_number = None
    code_snippet = None

    # Look for file references in traceback
    # Format: File "/path/to/file.py", line 123, in function_name
    for line in lines:
        file_match = re.search(r'File "([^"]+)",\s*line\s*(\d+)', line)
        if file_match:
            file_path = file_match.group(1)
            line_number = int(file_match.group(2))
            # The next line usually contains the code snippet
            idx = lines.index(line)
            if idx + 1 < len(lines):
                code_snippet = lines[idx + 1].strip()

    return PythonError(
        error_type=error_type,
        message=message,
        file=file_path,
        line=line_number,
        code_snippet=code_snippet,
        full_traceback=block,
    )


def _parse_standalone_errors(text: str) -> List[PythonError]:
    """
    Parse standalone error lines (e.g., from linters).

    Formats:
    - file.py:123: error message
    - file.py:123:45: E501 line too long
    """
    errors = []
    lines = text.strip().split("\n")

    for line in lines:
        # Pattern: file.py:line:col: error_type message
        match = re.match(
            r"^(.+?):(\d+)(?::(\d+))?:\s*(?:([A-Z]\d+)\s+)?(.+)$",
            line
        )
        if match:
            file_path = match.group(1)
            line_number = int(match.group(2))
            error_code = match.group(4) or "LintError"
            message = match.group(5)

            errors.append(
                PythonError(
                    error_type=error_code,
                    message=message,
                    file=file_path,
                    line=line_number,
                )
            )

    return errors


def extract_actionable_errors(errors: List[PythonError]) -> List[Dict]:
    """
    Extract actionable error information with suggestions.

    Args:
        errors: List of parsed errors

    Returns:
        List of error dictionaries with suggestions
    """
    actionable = []

    for error in errors:
        suggestion = _generate_error_suggestion(error)
        actionable.append({
            **error.to_dict(),
            "suggestion": suggestion,
            "actionable": suggestion is not None,
        })

    return actionable


def _generate_error_suggestion(error: PythonError) -> Optional[str]:
    """Generate fix suggestion for common Python errors."""
    error_type = error.error_type.lower()
    message = error.message.lower()

    # NameError: name 'x' is not defined
    if "nameerror" in error_type:
        match = re.search(r"name '([^']+)' is not defined", message)
        if match:
            name = match.group(1)
            return f"Import or define '{name}' before use. Check for typos in variable names."

    # ImportError / ModuleNotFoundError
    if "importerror" in error_type or "modulenotfounderror" in error_type:
        match = re.search(r"no module named '([^']+)'", message)
        if match:
            module = match.group(1)
            return f"Install missing module: pip install {module}"

    # TypeError
    if "typeerror" in error_type:
        if "missing" in message and "argument" in message:
            return "Check function call - missing required arguments"
        if "takes" in message and "positional argument" in message:
            return "Check function call - incorrect number of arguments"

    # AttributeError
    if "attributeerror" in error_type:
        match = re.search(r"'([^']+)' object has no attribute '([^']+)'", message)
        if match:
            obj_type = match.group(1)
            attr = match.group(2)
            return f"'{obj_type}' does not have attribute '{attr}'. Check spelling or object type."

    # SyntaxError
    if "syntaxerror" in error_type:
        return "Fix syntax error - check for missing colons, parentheses, or quotes"

    # IndentationError
    if "indentationerror" in error_type:
        return "Fix indentation - use consistent spaces (4 spaces recommended)"

    # KeyError
    if "keyerror" in error_type:
        return "Key not found in dictionary. Use .get() method or check key exists first."

    # IndexError
    if "indexerror" in error_type:
        return "List index out of range. Check list length before accessing."

    return None


def format_error_for_llm(error: PythonError) -> str:
    """
    Format error for LLM consumption.

    Args:
        error: Parsed Python error

    Returns:
        Formatted error string
    """
    parts = [f"❌ {error.error_type}: {error.message}"]

    if error.file and error.line:
        parts.append(f"📍 Location: {error.file}:{error.line}")

    if error.code_snippet:
        parts.append(f"💻 Code: {error.code_snippet}")

    suggestion = _generate_error_suggestion(error)
    if suggestion:
        parts.append(f"💡 Suggestion: {suggestion}")

    return "\n".join(parts)
