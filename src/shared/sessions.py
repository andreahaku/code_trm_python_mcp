"""Session management for TRM server."""

import uuid
from pathlib import Path
from typing import Dict, Optional
from ..types import (
    SessionId,
    SessionState,
    SessionConfig,
    SessionMode,
    CommandStatus,
    WeightsConfig,
)
from ..constants import (
    DEFAULT_WEIGHTS,
    DEFAULT_EMA_ALPHA,
)


# Global session storage
_sessions: Dict[SessionId, SessionState] = {}


def create_session(
    repo_path: str,
    data_quality_cmd: Optional[str],
    test_cmd: Optional[str],
    lint_cmd: Optional[str],
    perf_cmd: Optional[str],
    timeout_sec: int,
    weights: Optional[WeightsConfig],
    halt,  # Can be dict or HaltConfig
    ema_alpha: float,
    z_notes: Optional[str],
    mode: SessionMode = SessionMode.CUMULATIVE,
) -> SessionState:
    """
    Create a new TRM session.

    Args:
        repo_path: Path to repository
        data_quality_cmd: Command for data quality checks
        test_cmd: Command for running tests
        lint_cmd: Command for linting
        perf_cmd: Command for performance benchmarking
        timeout_sec: Timeout for commands
        weights: Evaluation weights
        halt: Halting policy configuration (dict or HaltConfig)
        ema_alpha: EMA smoothing factor
        z_notes: Initial reasoning notes
        mode: Session mode (cumulative/snapshot)

    Returns:
        New SessionState
    """
    from ..types import HaltConfig

    session_id = str(uuid.uuid4())

    # Convert halt to HaltConfig if needed
    if isinstance(halt, dict):
        halt = HaltConfig(**halt)

    # Create configuration
    config = SessionConfig(
        repo_path=repo_path,
        data_quality_cmd=data_quality_cmd,
        test_cmd=test_cmd,
        lint_cmd=lint_cmd,
        perf_cmd=perf_cmd,
        timeout_sec=timeout_sec,
        weights=weights or WeightsConfig(**DEFAULT_WEIGHTS),
        halt=halt,
    )

    # Initialize session state
    session = SessionState(
        id=session_id,
        cfg=config,
        created_at=0,  # Will be set in actual implementation
        step=0,
        best_score=0.0,
        ema_score=0.0,
        ema_alpha=ema_alpha or DEFAULT_EMA_ALPHA,
        no_improve_streak=0,
        history=[],
        z_notes=z_notes,
        best_perf=None,
        mode=mode,
        checkpoints={},
        baseline_commit=None,
        modified_files=set(),
        file_snapshots={},
        command_status={
            "data_quality": CommandStatus.UNKNOWN,
            "test": CommandStatus.UNKNOWN,
            "lint": CommandStatus.UNKNOWN,
            "perf": CommandStatus.UNKNOWN,
        },
        iteration_contexts=[],
        candidate_snapshots=[],
    )

    _sessions[session_id] = session
    return session


def get_session(session_id: SessionId) -> Optional[SessionState]:
    """Get session by ID."""
    return _sessions.get(session_id)


def delete_session(session_id: SessionId) -> bool:
    """Delete session by ID."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


def list_sessions() -> list[SessionId]:
    """List all active session IDs."""
    return list(_sessions.keys())


def validate_session_exists(session_id: SessionId) -> bool:
    """Check if session exists."""
    return session_id in _sessions


def update_session_state(session_id: SessionId, updates: dict) -> bool:
    """
    Update session state with partial updates.

    Args:
        session_id: Session ID
        updates: Dictionary of fields to update

    Returns:
        True if successful
    """
    session = _sessions.get(session_id)
    if not session:
        return False

    for key, value in updates.items():
        if hasattr(session, key):
            setattr(session, key, value)

    return True


def get_repo_path(session_id: SessionId) -> Optional[Path]:
    """Get repository path for session."""
    session = get_session(session_id)
    if not session:
        return None
    return Path(session.cfg.repo_path)
