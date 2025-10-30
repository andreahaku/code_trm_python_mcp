"""Constants for the TRM Python MCP server."""

# Default evaluation weights for data analysis
DEFAULT_WEIGHTS = {
    "data_quality": 0.3,  # Data validation, schema compliance
    "test": 0.4,  # Unit tests
    "lint": 0.1,  # Code quality (flake8, pylint, mypy)
    "perf": 0.2,  # Performance metrics
}

# Default halting policy
DEFAULT_HALT = {
    "max_steps": 12,
    "pass_threshold": 0.95,
    "patience_no_improve": 3,
    "min_steps": 1,
}

# Default EMA alpha for score smoothing
DEFAULT_EMA_ALPHA = 0.9

# Command timeout in seconds
DEFAULT_TIMEOUT = 120

# Supported Python file extensions
PYTHON_EXTENSIONS = [".py", ".ipynb"]

# Default exclude patterns for file operations
DEFAULT_EXCLUDE_PATTERNS = [
    "**/__pycache__/**",
    "**/venv/**",
    "**/.venv/**",
    "**/env/**",
    "**/.env/**",
    "**/node_modules/**",
    "**/.git/**",
    "**/build/**",
    "**/dist/**",
    "**/*.pyc",
    "**/.pytest_cache/**",
    "**/.mypy_cache/**",
    "**/__pycache__/**",
]

# Maximum snapshot history for undo
MAX_CANDIDATE_SNAPSHOTS = 10

# Maximum checkpoint storage
MAX_CHECKPOINTS = 20
