# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

## Development Commands

### Running the Server

```bash
# Development mode (from repo root)
python -m src.server

# After installation
pip install -e .
code-trm-python-mcp
```

### Testing and Quality Checks

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (once implemented)
pytest tests/

# Format code
black src/
isort src/

# Type checking
mypy src/

# Lint code
flake8 src/
pylint src/
```

### MCP Configuration

Add to your MCP client (e.g., Claude Code) configuration:

```json
{
  "mcpServers": {
    "code-trm-python": {
      "command": "python",
      "args": ["-m", "src.server"]
    }
  }
}
```

Or after installation:

```json
{
  "mcpServers": {
    "code-trm-python": {
      "command": "code-trm-python-mcp"
    }
  }
}
```

## Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      LLM Client                              │
│         (Claude Code / Cursor / Codex CLI)                  │
│                                                              │
│  • Proposes code changes (optimizer role)                   │
│  • Submits candidates via MCP tools                         │
│  • Interprets feedback and iterates                         │
└────────────────────┬────────────────────────────────────────┘
                     │ MCP Protocol
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              TRM Python MCP Server                          │
│                                                              │
│  Session State:                                             │
│  • Current score, EMA, best score                           │
│  • Test results, data quality status                        │
│  • Improvement streak tracking                              │
│  • History of evaluations                                   │
│  • Candidate snapshots (for undo)                           │
│                                                              │
│  Evaluation Pipeline:                                       │
│  1. Apply candidate changes                                 │
│  2. Run: data_quality → test → lint → perf                  │
│  3. Parse outputs, extract signals                          │
│  4. Compute weighted score                                  │
│  5. Update EMA and improvement tracking                     │
│  6. Check halting policy                                    │
│  7. Return structured feedback                              │
└────────────────────┬────────────────────────────────────────┘
                     │ Shell Commands
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Target Python Project                          │
│                                                              │
│  • Source code files (.py, .ipynb)                          │
│  • Data validation scripts                                  │
│  • Test framework (pytest, unittest)                        │
│  • Linters (flake8, pylint, mypy)                           │
│  • Performance benchmark scripts                            │
│  • Data analysis pipelines (pandas, numpy)                  │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. MCP Server Layer (`src/server.py`)

**Entry point** for all MCP protocol communication.

- Handles 16 tools via async handlers
- Uses `translate_params()` to convert short → long parameter names for token efficiency
- Routes tool calls to specialized handlers

**Key handler pattern:**
```python
async def handle_tool_call(name: str, arguments: dict) -> list[TextContent]:
    # 1. Translate short params to long params (src/tools/param_translator.py)
    args = translate_params(name, arguments)

    # 2. Route to specific handler
    if name == "trm.start":
        return await handle_start_session(args)
    elif name == "trm.submit":
        return await handle_submit_candidate(args)
    # ... etc
```

#### 2. Type System (`src/types.py`)

**All data structures use dataclasses** for type safety and clarity.

Key types:
- `SessionState`: Complete session state (includes cfg, step, scores, history)
- `EvalResult`: Single evaluation result with scores and feedback
- `WeightsConfig`: Evaluation signal weights (data_quality, test, lint, perf)
- `HaltConfig`: Halting policy (max_steps, pass_threshold, patience_no_improve)
- `TestResults`, `PerfResults`: Parsed evaluation signals
- `CandidateSnapshot`: For undo functionality

**Pattern:** All function signatures use these types for clarity. When modifying, maintain dataclass patterns.

#### 3. Parameter Translation (`src/tools/param_translator.py`)

**Token optimization layer** - MCP tools use short parameter names, internal code uses descriptive names.

Mapping examples:
- `sid` → `session_id`
- `repo` → `repo_path`
- `dataQual` → `data_quality_cmd`
- `bench` → `perf_cmd`

When adding new tools, add translation here.

#### 4. Evaluation Pipeline (`src/tools/handlers/lib/evaluation.py`)

**Core evaluation logic** that runs after each candidate submission.

Flow in `run_evaluation()`:
1. Run data quality checks (if configured) → `ok_data_quality: bool`
2. Run tests (pytest/unittest) → `TestResults(passed, failed, total)`
3. Run lint (flake8/pylint/mypy) → `ok_lint: bool`
4. Run performance benchmark → `PerfResults(value, unit)`
5. Calculate weighted score via `scoring.calculate_weighted_score()`
6. Update EMA via `scoring.update_ema_score()`
7. Check halting via `scoring.should_halt_iteration()`
8. Update session state and return `EvalResult`

**Important:** Commands run in the target repo directory with configurable timeout.

#### 5. Scoring & Halting (`src/utils/scoring.py`)

**Three key functions:**

1. **`calculate_weighted_score()`**: Computes weighted average in [0, 1]
   ```python
   score = (w.dataQual * s_dataQual + w.test * s_tests +
            w.lint * s_lint + w.perf * s_perf) / sum_weights

   where:
     s_dataQual = 1 if pass, 0 otherwise
     s_tests = passed / total
     s_lint = 1 if pass, 0 otherwise
     s_perf = best / current (normalized, lower is better)
   ```

2. **`update_ema_score()`**: EMA = alpha * current + (1 - alpha) * prev_ema

3. **`should_halt_iteration()`**: Returns (bool, reasons) based on:
   - **Success**: step >= min_steps AND tests pass AND score >= threshold
   - **Plateau**: no improvement for patience steps
   - **Limit**: reached max_steps

#### 6. Session Management (`src/shared/sessions.py`)

Global session storage using in-memory dictionary:
- `_sessions: Dict[SessionId, SessionState]`
- `create_session()`, `get_session()`, `delete_session()`
- Sessions persist only during server runtime (no disk persistence)

#### 7. Python Error Parsing (`src/utils/py_error_parser.py`)

Parses Python tracebacks and lint errors:

- **Traceback parsing**: Extracts error type, message, file, line, code snippet
- **Actionable suggestions**:
  - NameError → "Import or define 'x' before use"
  - ImportError → "pip install module_name"
  - TypeError → "Check function arguments"
  - AttributeError → "Check attribute spelling"
- **Lint error parsing**: Handles flake8/pylint output format

Use `format_error_for_llm()` to generate user-friendly error messages.

#### 8. Test & Performance Parsing (`src/utils/parser.py`)

Extracts signals from command output:
- `parse_test_output()`: pytest JSON format, unittest text format
- `parse_performance_metric()`: Extracts numeric values (seconds, ms)

### Tool Schema Design (`src/tools/schemas.py`)

**16 MCP tools** organized as:
- **Core** (6): start, submit, read, state, halt, end
- **Enhancement** (3): validate, suggest, review
- **Checkpoint** (4): save, restore, list, reset
- **Advanced** (3): undo, lines, fix

All schemas use short parameter names for token efficiency. Descriptions are concise.

## Implementation Status

### ✅ Fully Implemented

- Core types and data structures (src/types.py)
- Session management (src/shared/sessions.py)
- Scoring and EMA tracking (src/utils/scoring.py)
- Evaluation pipeline (src/tools/handlers/lib/evaluation.py)
- Python error parser with suggestions (src/utils/py_error_parser.py)
- Test output parsers (src/utils/parser.py)
- Command execution utilities (src/utils/command.py)
- MCP server with 16 tool handlers (src/server.py)
- Parameter translation layer (src/tools/param_translator.py)

### 🚧 To Be Implemented

The following have placeholder handlers that return "not implemented yet":

- **File patching** (src/patcher/): Apply diffs/patches/edits to files
- **Candidate validation** (trm.validate): Dry-run before applying
- **Checkpoint management** (trm.save/restore/list): Save/restore session state
- **Baseline reset** (trm.reset): Reset repo to git baseline
- **Undo** (trm.undo): Revert last candidate
- **AI suggestions** (trm.fix, trm.suggest): Generate fix candidates
- **PR review** (trm.review): Analyze pull requests
- **Code analysis** (src/analyzer/): For generating suggestions
- **File line reading** (trm.lines): Read specific line ranges

When implementing these, follow the existing patterns in src/server.py handler functions.

## Data Analysis Focus

### Evaluation Signals

**1. Data Quality (default weight: 0.3)**
- Custom validation scripts
- Pandas DataFrame schema validation
- Missing value checks
- Data type consistency
- Example: `python scripts/validate_schemas.py`

**2. Tests (default weight: 0.4)**
- pytest with JSON output (`pytest --json tests/`)
- unittest support
- Parses passed/failed/total
- Binary pass/fail for halting logic

**3. Lint (default weight: 0.1)**
- flake8 for PEP 8 compliance
- pylint for code quality
- mypy for type hints
- Example: `flake8 src/ && mypy src/`

**4. Performance (default weight: 0.2)**
- Runtime benchmarks
- Memory profiling
- Normalized scoring (best/current)
- Example: `python scripts/benchmark_pipeline.py`

### Weight Configuration

Adjust weights based on task priority:
- **Algorithm correctness**: Increase `test` weight (e.g., 0.6)
- **Data pipeline reliability**: Increase `dataQual` weight (e.g., 0.5)
- **Optimization tasks**: Increase `perf` weight (e.g., 0.4)
- **Code quality**: Increase `lint` weight (e.g., 0.3)

Weights don't need to sum to 1.0 - they're normalized automatically.

## How to Extend

### Adding a New Tool

Follow this 4-step pattern:

1. **Define schema** in `src/tools/schemas.py`:
   ```python
   Tool(
       name="trm.newTool",
       description="Short description",
       inputSchema={
           "type": "object",
           "properties": {
               "sid": {"type": "string", "description": "Session ID"},
               # ... other params
           },
           "required": ["sid"]
       }
   )
   ```

2. **Add parameter translation** in `src/tools/param_translator.py`:
   ```python
   def translate_params(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
       # ...
       elif tool_name == "trm.newTool":
           return _translate_new_tool(args)

   def _translate_new_tool(args: Dict[str, Any]) -> Dict[str, Any]:
       return {
           "session_id": args.get("sid"),
           # ... map short → long names
       }
   ```

3. **Implement handler** in `src/server.py`:
   ```python
   async def handle_new_tool(args: dict) -> list[TextContent]:
       session = get_session(args["session_id"])
       if not session:
           return [TextContent(type="text", text=json.dumps({"error": "Session not found"}, indent=2))]

       # Implementation
       result = {"key": "value"}
       return [TextContent(type="text", text=json.dumps(result, indent=2))]
   ```

4. **Route in main handler**:
   ```python
   async def handle_tool_call(name: str, arguments: dict) -> list[TextContent]:
       args = translate_params(name, arguments)
       # ...
       elif name == "trm.newTool":
           return await handle_new_tool(args)
   ```

### Adding New Evaluation Signal

Example: Adding security scanning

1. **Update `WeightsConfig`** in `src/types.py`:
   ```python
   @dataclass
   class WeightsConfig:
       data_quality: float = 0.3
       test: float = 0.4
       lint: float = 0.1
       perf: float = 0.2
       security: float = 0.1  # New signal
   ```

2. **Update scoring** in `src/utils/scoring.py`:
   ```python
   def calculate_weighted_score(
       # ... existing params
       ok_security: Optional[bool],
       weights: WeightsConfig,
   ) -> float:
       # ... existing code

       # Security signal
       if ok_security is not None:
           s_security = 1.0 if ok_security else 0.0
           components.append(weights.security * s_security)
           total_weight += weights.security
   ```

3. **Add command execution** in `src/tools/handlers/lib/evaluation.py`:
   ```python
   async def run_evaluation(session: SessionState) -> EvalResult:
       # ... existing signals

       # 5. Run security scan
       ok_security = None
       if session.cfg.security_cmd:
           result = await run_command(
               session.cfg.security_cmd,
               repo_path,
               timeout,
           )
           ok_security = result.ok
           feedback.append("✅ Security scan passed" if result.ok else "❌ Security issues found")

       # Update score calculation
       score = calculate_weighted_score(
           # ... existing params
           ok_security=ok_security,
           weights=session.cfg.weights,
       )
   ```

4. **Update `SessionConfig`** in `src/types.py`:
   ```python
   @dataclass
   class SessionConfig:
       # ... existing fields
       security_cmd: Optional[str]
   ```

## Key Implementation Patterns

### 1. Async Command Execution

All shell commands must use `run_command()` from `src/utils/command.py`:

```python
from src.utils.command import run_command

result = await run_command(
    command="pytest --json tests/",
    cwd=Path("/path/to/repo"),
    timeout_sec=120
)

# Result is CommandResult(ok: bool, stdout: str, stderr: str, exit_code: int)
```

### 2. Error Handling

All handlers should catch exceptions and return error JSON:

```python
try:
    # Handler logic
    return [TextContent(type="text", text=json.dumps(result, indent=2))]
except Exception as e:
    return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]
```

### 3. Session Validation

Always validate session exists:

```python
session = get_session(args["session_id"])
if not session:
    return [TextContent(type="text", text=json.dumps({"error": "Session not found"}, indent=2))]
```

### 4. Dataclass Usage

Prefer dataclasses over dicts for structured data:

```python
# Good
@dataclass
class MyResult:
    value: float
    message: str

result = MyResult(value=0.95, message="Success")

# Avoid
result = {"value": 0.95, "message": "Success"}
```

### 5. Output Parsing

Use dedicated parsers for consistency:

```python
from src.utils.parser import parse_test_output, parse_performance_metric

# Parse test output
tests = parse_test_output(stdout + "\n" + stderr, "pytest")
if tests:
    pass_rate = tests.passed / tests.total

# Parse performance metric
perf_value = parse_performance_metric(output)
if perf_value is not None:
    perf = PerfResults(value=perf_value, unit="seconds")
```

## Common Development Tasks

### Debugging Session State

Sessions are stored in `src/shared/sessions.py`:

```python
from src.shared.sessions import _sessions

# View all sessions
print(_sessions)

# Get specific session
session = _sessions.get("session-id-123")
if session:
    print(f"Step: {session.step}, Score: {session.ema_score}")
```

### Testing a Single Tool

```python
import asyncio
from src.server import handle_tool_call

async def test():
    # Start session
    result = await handle_tool_call("trm.start", {
        "repo": "/path/to/project",
        "test": "pytest tests/",
        "halt": {"max": 5, "threshold": 0.9, "patience": 2}
    })
    print(result[0].text)

asyncio.run(test())
```

### Examining Evaluation Results

```python
session = get_session("session-id")
if session.history:
    last_eval = session.history[-1]
    print(f"Score: {last_eval.score}")
    print(f"Feedback: {last_eval.feedback}")
    print(f"Should halt: {last_eval.should_halt}")
    print(f"Reasons: {last_eval.reasons}")
```

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

## Tips for Development

1. **Read before modifying**: Always read existing code to understand patterns
2. **Maintain parameter translation**: Keep short names in MCP layer, long names internally
3. **Follow dataclass patterns**: Use dataclasses for all structured data
4. **Use async/await**: All command execution is async
5. **Parse output carefully**: pytest/unittest have different formats
6. **Configure weights thoughtfully**: Adjust for task (testing vs performance vs data quality)
7. **EMA smoothing**: Helps avoid score noise, alpha typically 0.9
8. **Halting policy**: Prevents infinite loops, typical max_steps: 12, threshold: 0.95
9. **Token efficiency**: Short parameter names in MCP tools save tokens
10. **Error feedback**: Provide actionable suggestions using `py_error_parser.py`

## Useful References

- Original TRM paper: arXiv:2510.04871v1
- MCP protocol: https://modelcontextprotocol.io
- TypeScript version: https://github.com/andreahaku/code_trm_mcp
- Related: llm-memory-mcp, code-analysis-context-python-mcp (same author)

---

**Last Updated**: 2025-10-30
**Status**: Beta - Core functionality implemented, advanced features in progress
**Python Version**: 3.10+
