"""Type definitions for the TRM Python MCP server."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Set, Union

SessionId = str


# ============= CORE REQUEST/RESPONSE TYPES =============

@dataclass
class HaltConfig:
    """Halting policy configuration."""

    max_steps: int
    pass_threshold: float
    patience_no_improve: int
    min_steps: int = 1


@dataclass
class WeightsConfig:
    """Evaluation weights configuration."""

    data_quality: float = 0.3
    test: float = 0.4
    lint: float = 0.1
    perf: float = 0.2


@dataclass
class StartSessionArgs:
    """Arguments for starting a TRM session."""

    repo_path: str
    data_quality_cmd: Optional[str] = None
    test_cmd: Optional[str] = None
    lint_cmd: Optional[str] = None
    perf_cmd: Optional[str] = None
    timeout_sec: int = 120
    weights: Optional[WeightsConfig] = None
    halt: HaltConfig = None
    ema_alpha: float = 0.9
    z_notes: Optional[str] = None
    preflight: bool = False


@dataclass
class FileMetadata:
    """File metadata information."""

    line_count: int
    size_bytes: int
    last_modified: str  # ISO timestamp


@dataclass
class FileWithMetadata:
    """File content with metadata."""

    content: str
    metadata: FileMetadata


@dataclass
class GetFileContentArgs:
    """Arguments for getting file content."""

    session_id: str
    paths: List[str]
    offset: Optional[int] = None  # Line number to start from (1-based)
    limit: Optional[int] = None  # Maximum number of lines to return


@dataclass
class GetFileContentResponse:
    """Response containing file contents."""

    files: Dict[str, FileWithMetadata]


# ============= CANDIDATE SUBMISSION TYPES =============

@dataclass
class DiffChange:
    """Per-file diff change."""

    path: str
    diff: str


@dataclass
class FileContent:
    """Complete file content."""

    path: str
    content: str


@dataclass
class EditOperation:
    """Semantic edit operation."""

    type: Literal[
        "replace", "insertBefore", "insertAfter", "replaceLine",
        "replaceRange", "deleteLine", "deleteRange"
    ]
    old_text: Optional[str] = None
    new_text: Optional[str] = None
    line: Optional[int] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    content: Optional[str] = None
    all: bool = False  # For replace: replace all occurrences


@dataclass
class ModifyChange:
    """File modification with semantic edits."""

    file: str
    edits: List[EditOperation]


CandidateMode = Literal["diff", "patch", "files", "modify", "create"]


@dataclass
class SubmitCandidateArgs:
    """Arguments for submitting a candidate."""

    session_id: str
    candidate: Union[
        Dict[str, Any],  # Generic dict that will be validated
    ]
    rationale: Optional[str] = None


# ============= SESSION STATE TYPES =============

@dataclass
class SessionConfig:
    """Session configuration."""

    repo_path: str
    data_quality_cmd: Optional[str]
    test_cmd: Optional[str]
    lint_cmd: Optional[str]
    perf_cmd: Optional[str]
    timeout_sec: int
    weights: WeightsConfig
    halt: HaltConfig


@dataclass
class ModeSuggestion:
    """Suggestion for submission mode."""

    recommended: str
    reason: str
    confidence: Literal["high", "medium", "low"]
    alternatives: Optional[Dict[str, str]] = None


@dataclass
class TestResults:
    """Test execution results."""

    passed: int
    failed: int
    total: int
    raw: Optional[str] = None


@dataclass
class PerfResults:
    """Performance metrics."""

    value: float
    unit: Optional[str] = None


@dataclass
class EvalResult:
    """Evaluation result from a single iteration."""

    ok_data_quality: Optional[bool] = None
    ok_lint: Optional[bool] = None
    tests: Optional[TestResults] = None
    perf: Optional[PerfResults] = None
    score: float = 0.0
    ema_score: float = 0.0
    step: int = 0
    feedback: List[str] = field(default_factory=list)
    should_halt: bool = False
    reasons: List[str] = field(default_factory=list)
    mode_suggestion: Optional[ModeSuggestion] = None


class SessionMode(Enum):
    """Session mode."""

    CUMULATIVE = "cumulative"
    SNAPSHOT = "snapshot"


class CommandStatus(Enum):
    """Command availability status."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class Checkpoint:
    """Session checkpoint."""

    id: str
    timestamp: float
    step: int
    score: float
    ema_score: float
    files_snapshot: Dict[str, str]
    description: Optional[str] = None


@dataclass
class IterationContext:
    """Context for a single iteration."""

    step: int
    files_modified: List[str]
    mode: str
    success: bool


@dataclass
class CandidateSnapshot:
    """Snapshot of a candidate submission for undo."""

    step: int
    candidate: Any
    rationale: Optional[str]
    files_before_change: Dict[str, str]
    eval_result: EvalResult
    timestamp: float


@dataclass
class SessionState:
    """Complete session state."""

    id: SessionId
    cfg: SessionConfig
    created_at: float
    step: int
    best_score: float
    ema_score: float
    ema_alpha: float
    no_improve_streak: int
    history: List[EvalResult]
    z_notes: Optional[str]
    best_perf: Optional[float]
    mode: SessionMode
    checkpoints: Dict[str, Checkpoint]
    baseline_commit: Optional[str]
    modified_files: Set[str]
    file_snapshots: Dict[str, str]
    command_status: Dict[str, CommandStatus]
    iteration_contexts: List[IterationContext]
    candidate_snapshots: List[CandidateSnapshot]


# ============= ENHANCED API TYPES =============

@dataclass
class UndoLastCandidateArgs:
    """Arguments for undo operation."""

    session_id: str


@dataclass
class GetFileLinesArgs:
    """Arguments for getting specific file lines."""

    session_id: str
    file: str
    start_line: int  # 1-based, inclusive
    end_line: int  # 1-based, inclusive


@dataclass
class GetFileLinesResponse:
    """Response with specific file lines."""

    file: str
    lines: List[str]  # Lines with line numbers
    line_count: int  # Total line count of the file


@dataclass
class SuggestFixArgs:
    """Arguments for fix suggestion."""

    session_id: str


@dataclass
class FixSuggestion:
    """AI-generated fix suggestion."""

    priority: Literal["critical", "high", "medium", "low"]
    issue: str
    candidate_to_fix: Dict[str, Any]  # Ready-to-apply candidate
    rationale: str


@dataclass
class SuggestFixResponse:
    """Response with fix suggestions."""

    suggestions: List[FixSuggestion]


@dataclass
class Suggestion:
    """Code improvement suggestion."""

    priority: Literal["critical", "high", "medium", "low"]
    category: Literal[
        "type-safety", "documentation", "performance",
        "test-coverage", "code-quality", "security", "data-validation"
    ]
    issue: str
    locations: Optional[List[Dict[str, Any]]] = None
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class CodeIssue:
    """Detected code issue."""

    type: Literal[
        "any-type", "missing-docstring", "magic-number", "long-function",
        "high-complexity", "no-error-handling", "large-module", "deep-nesting",
        "impure-function", "hard-to-mock", "missing-type-hints", "data-validation-missing"
    ]
    severity: Literal["error", "warning", "info"]
    file: str
    line: Optional[int] = None
    column: Optional[int] = None
    message: str = ""
    context: Optional[str] = None


@dataclass
class EnhancedError:
    """Enhanced error with context."""

    error: str
    code: str
    details: Dict[str, Any]


@dataclass
class FilePreview:
    """Preview of file changes."""

    file: str
    before_lines: List[str]
    after_lines: List[str]
    lines_added: int
    lines_removed: int
    change_type: Literal["insertion", "deletion", "modification", "replacement"]


@dataclass
class ValidationResult:
    """Result of candidate validation."""

    valid: bool
    errors: List[EnhancedError]
    warnings: List[str]
    preview: Optional[Dict[str, Any]] = None


@dataclass
class SaveCheckpointArgs:
    """Arguments for saving checkpoint."""

    session_id: str
    description: Optional[str] = None


@dataclass
class RestoreCheckpointArgs:
    """Arguments for restoring checkpoint."""

    session_id: str
    checkpoint_id: str


@dataclass
class ListCheckpointsArgs:
    """Arguments for listing checkpoints."""

    session_id: str


# ============= UTILITY TYPES =============

@dataclass
class CommandResult:
    """Result from shell command execution."""

    ok: bool
    stdout: str
    stderr: str
    exit_code: Optional[int]


@dataclass
class ParsedDiffHunk:
    """Parsed diff hunk."""

    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: List[Dict[str, str]]  # {type: "context"|"add"|"remove", content: str}


@dataclass
class ParsedDiffFile:
    """Parsed diff file."""

    file: str
    hunks: List[ParsedDiffHunk]


# ============= PR REVIEW TYPES =============

@dataclass
class PRReviewArgs:
    """Arguments for PR review."""

    pr_url: Optional[str] = None
    diff: Optional[str] = None
    files: Optional[List[Dict[str, Any]]] = None
    focus: Optional[List[str]] = None


@dataclass
class ReviewComment:
    """Review comment."""

    file: str
    line: int
    severity: Literal["error", "warning", "info"]
    category: Literal[
        "type-safety", "logging", "todos", "code-quality",
        "formatting", "error-handling", "testing", "size", "data-validation"
    ]
    message: str
    suggestion: Optional[str] = None


@dataclass
class ReviewSummary:
    """PR review summary."""

    files_changed: int
    lines_added: int
    lines_removed: int
    comments_count: int
    critical_count: int
    warning_count: int
    info_count: int
    assessment: Literal["approved", "needs-changes", "comments"]
    highlights: List[str]


@dataclass
class PRReviewResponse:
    """PR review response."""

    summary: ReviewSummary
    comments: List[ReviewComment]
    issues: List[str]
    suggestions: List[str]
    pr_info: Optional[Dict[str, Any]] = None
