# CLAUDE.md - Guide for Future Claude Code Instances

## Project Overview

**code_trm_python_mcp** is a TRM (Test-time Recursive Memory) MCP server implemented in Python, specifically designed for iterative code refinement in data analysis projects.

### Core Concept

This server implements a recursive improvement cycle:
1. **LLM (optimizer)** proposes code changes via MCP tools
2. **Server (critic)** evaluates changes using multi-signal evaluation
3. **Weighted scoring** with EMA tracking measures improvement
4. **Halting policy** determines when to stop iterating

### Key Differentiator

Unlike the TypeScript version (`code_trm_mcp`), this implementation is **Python-focused** with special support for:
- Data analysis workflows (Pandas, NumPy, Scikit-learn)
- Python error parsing (tracebacks)
- pytest/unittest integration
- Data quality validation
- Python-specific linting (flake8, pylint, mypy)

## Architecture

### Project Structure

```
code_trm_python_mcp/
├── src/
│   ├── server.py              # MCP server entry point, tool handlers
│   ├── types.py                # Type definitions (dataclasses)
│   ├── constants.py            # Default configuration
│   ├── tools/
│   │   ├── schemas.py          # MCP tool definitions (16 tools)
│   │   ├── param_translator.py # Short → long parameter names
│   │   └── handlers/
│   │       └── lib/
│   │           └── evaluation.py  # Core evaluation pipeline
│   ├── shared/
│   │   └── sessions.py         # Session management
│   ├── utils/
│   │   ├── scoring.py          # Weighted scoring, EMA, halting logic
│   │   ├── command.py          # Async command execution
│   │   ├── parser.py           # Test output parsing
│   │   └── py_error_parser.py  # Python traceback parsing
│   ├── patcher/                # File patching (to be implemented)
│   ├── analyzer/               # Code analysis (to be implemented)
│   └── state/                  # Checkpoints, baselines (to be implemented)
├── pyproject.toml
├── README.md
└── CLAUDE.md (this file)
```

### Core Components

#### 1. Server (`src/server.py`)

- **Main entry point** for MCP protocol
- Defines async tool handlers for all 16 tools
- Uses `translate_params()` to convert short → long parameter names
- Delegates to specialized handlers

**Key handlers:**
- `handle_start_session`: Initialize TRM session
- `handle_submit_candidate`: Apply changes + run evaluation
- `handle_get_file_content`: Read files from repo
- `handle_get_state`: Return session state snapshot
- `handle_should_halt`: Check halting decision

#### 2. Types (`src/types.py`)

- **Dataclasses** for all data structures
- Key types:
  - `SessionState`: Complete session state
  - `EvalResult`: Evaluation result with scores
  - `WeightsConfig`: Evaluation weights
  - `HaltConfig`: Halting policy configuration

#### 3. Evaluation Pipeline (`src/tools/handlers/lib/evaluation.py`)

**Core logic:**
```python
async def run_evaluation(session: SessionState) -> EvalResult:
    # 1. Run data quality checks (if configured)
    # 2. Run tests (pytest/unittest)
    # 3. Run lint (flake8, pylint, mypy)
    # 4. Run performance benchmark
    # 5. Calculate weighted score
    # 6. Update EMA
    # 7. Check halting condition
    # 8. Return EvalResult
```

**Scoring formula:**
```
score = (w.dataQual * sDataQual + w.test * sTests +
         w.lint * sLint + w.perf * sPerf) / sumWeights

where:
  sDataQual = 1 if pass, 0 otherwise
  sTests = passed / total
  sLint = 1 if pass, 0 otherwise
  sPerf = best / current (normalized, lower is better)
```

#### 4. Session Management (`src/shared/sessions.py`)

- **Global session storage**: `_sessions: Dict[SessionId, SessionState]`
- CRUD operations: `create_session`, `get_session`, `delete_session`
- Session validation and updates

#### 5. Scoring & Halting (`src/utils/scoring.py`)

**Three key functions:**

1. `calculate_weighted_score()`: Compute weighted average from signals
2. `update_ema_score()`: EMA = alpha * current + (1 - alpha) * prev_ema
3. `should_halt_iteration()`: Check three halting conditions:
   - **Success**: tests pass + score >= threshold + step >= minSteps
   - **Plateau**: no improvement for patience steps
   - **Limit**: reached maxSteps

## MCP Tools (16 Total)

### Tool Schema Design

**Token optimization:**
- Short parameter names in MCP layer (e.g., `sid`, `repo`, `dataQual`)
- `param_translator.py` converts to long names internally (e.g., `session_id`, `repo_path`, `data_quality_cmd`)
- Concise descriptions

### Core Tools (6)

1. **trm.start**: Initialize session with repo path, commands, halt policy
2. **trm.submit**: Submit candidate, run evaluation, return scores/feedback
3. **trm.read**: Get file contents with metadata
4. **trm.state**: Get session state snapshot
5. **trm.halt**: Check halting decision
6. **trm.end**: Clean up session

### Enhancement Tools (3)

7. **trm.validate**: Dry-run validation before applying
8. **trm.suggest**: AI-powered improvement suggestions
9. **trm.review**: PR review from URL or diff

### Checkpoint Tools (4)

10. **trm.save**: Save checkpoint
11. **trm.restore**: Restore from checkpoint
12. **trm.list**: List checkpoints
13. **trm.reset**: Reset to baseline

### Advanced Tools (3)

14. **trm.undo**: Undo last candidate
15. **trm.lines**: Read specific line range
16. **trm.fix**: AI-powered fix suggestions

## Implementation Status

### ✅ Completed

- Core types and data structures
- Session management
- Scoring and EMA tracking
- Evaluation pipeline (data_quality, test, lint, perf)
- Python error parser (traceback parsing)
- Test output parsers (pytest, unittest)
- Command execution utilities
- MCP server with 16 tool handlers
- Parameter translation (short → long names)
- Comprehensive README

### 🚧 To Be Implemented

- File patching (apply diffs/patches to files)
- Candidate validation (dry-run before applying)
- Checkpoint save/restore
- Baseline reset (git integration)
- Undo functionality
- AI-powered fix generation
- PR review logic
- Code analysis for suggestions
- File line reading utility

## Data Analysis Focus

### Evaluation Signals

**1. Data Quality (weight: 0.3)**
- Run custom validation scripts
- Check Pandas DataFrame schemas
- Validate data types, missing values
- Example command: `python scripts/validate_data.py`

**2. Tests (weight: 0.4)**
- pytest with JSON output parsing
- unittest support
- Parse test results: passed/failed/total
- Example command: `pytest --json tests/`

**3. Lint (weight: 0.1)**
- flake8 for style checking
- pylint for code quality
- mypy for type hints
- Example command: `flake8 src/ && mypy src/`

**4. Performance (weight: 0.2)**
- Run benchmark scripts
- Parse numeric output (seconds, ms)
- Track best performance, detect regressions
- Example command: `python scripts/benchmark.py`

### Python Error Parsing

`src/utils/py_error_parser.py` parses Python tracebacks:

- **NameError** → suggests imports or variable definitions
- **ImportError** → suggests `pip install` commands
- **TypeError** → identifies argument mismatches
- **AttributeError** → detects incorrect attribute access
- **SyntaxError** → highlights syntax issues
- **Lint errors** → parses flake8/pylint output

## How to Extend

### Adding a New Tool

1. **Define schema** in `src/tools/schemas.py`:
```python
Tool(
    name="trm.newTool",
    description="Short description",
    inputSchema={...}
)
```

2. **Add parameter translation** in `src/tools/param_translator.py`:
```python
def translate_params(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "trm.newTool":
        return _translate_new_tool(args)
```

3. **Implement handler** in `src/server.py`:
```python
async def handle_new_tool(args: dict) -> list[TextContent]:
    session = get_session(args["session_id"])
    # ... implementation
    return [TextContent(type="text", text=json.dumps(result, indent=2))]
```

4. **Route in main handler**:
```python
async def handle_tool_call(name: str, arguments: dict) -> list[TextContent]:
    if name == "trm.newTool":
        return await handle_new_tool(args)
```

### Adding New Evaluation Signal

1. **Update `WeightsConfig`** in `src/types.py`:
```python
@dataclass
class WeightsConfig:
    data_quality: float = 0.3
    test: float = 0.4
    lint: float = 0.1
    perf: float = 0.2
    new_signal: float = 0.1  # Add new signal
```

2. **Update scoring** in `src/utils/scoring.py`:
```python
def calculate_weighted_score(..., new_signal_value: Optional[bool]):
    # Add new signal to score calculation
```

3. **Add command execution** in `src/tools/handlers/lib/evaluation.py`:
```python
async def run_evaluation(session: SessionState) -> EvalResult:
    # ... existing signals

    # New signal
    if session.cfg.new_signal_cmd:
        result = await run_command(session.cfg.new_signal_cmd, ...)
        # Parse and add to EvalResult
```

## Common Tasks

### Running the Server

```bash
# Development mode
python -m src.server

# Installed mode
code-trm-python-mcp
```

### Testing a Tool

```python
import asyncio
from src.server import handle_tool_call

async def test():
    result = await handle_tool_call("trm.start", {
        "repo": "/path/to/project",
        "test": "pytest tests/",
        "halt": {"max": 5, "threshold": 0.9, "patience": 2}
    })
    print(result[0].text)

asyncio.run(test())
```

### Debugging

- Session state in `_sessions` global dict in `src/shared/sessions.py`
- Add print statements in handlers to trace execution
- Check `stderr` in command execution for error details

## Key Differences from TypeScript Version

| Feature | TypeScript (code_trm_mcp) | Python (code_trm_python_mcp) |
|---------|---------------------------|------------------------------|
| **Language** | TypeScript/JavaScript | Python |
| **Focus** | General web dev | Data analysis |
| **Build signal** | TypeScript compilation | Data quality checks |
| **Test frameworks** | Jest, Vitest | pytest, unittest |
| **Linting** | ESLint | flake8, pylint, mypy |
| **Error parsing** | TS errors (TS2304, etc.) | Python tracebacks |
| **File types** | .ts, .js, .tsx, .jsx | .py, .ipynb |
| **Dependencies** | npm packages | pip packages |

## Tips for Future Instances

1. **Always read existing code first** before modifying
2. **Maintain parameter translation** - keep short names in MCP layer
3. **Follow dataclass patterns** in types.py
4. **Use async/await** for all command execution
5. **Parse output carefully** - pytest/unittest have different formats
6. **Weight configuration matters** - adjust for task (testing vs performance)
7. **EMA smoothing** helps avoid noise in scores
8. **Halting policy** prevents infinite loops

## Useful References

- Original TRM paper: arXiv:2510.04871v1
- MCP protocol: https://modelcontextprotocol.io
- TypeScript version: https://github.com/andreahaku/code_trm_mcp
- Related: code-analysis-context-python-mcp (same author)

---

**Last Updated**: 2025-10-30
**Status**: Beta - Core functionality implemented
