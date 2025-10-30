# TRM Python MCP Server

A **TRM-inspired (Test-time Recursive Memory) MCP server** for recursive code refinement in Python data analysis projects.

This server implements a recursive improvement cycle specifically designed for Python and data analysis workflows:
- The LLM acts as the **optimizer** proposing code changes
- This MCP server acts as the **critic/evaluator** with stateful tracking
- Evaluations include: **data quality checks, tests, lint, and performance metrics**
- Scores are tracked using EMA (Exponential Moving Average)
- An intelligent halting policy determines when to stop

## ✨ Features

- **Multi-signal evaluation**: Data quality, tests, lint, and performance benchmarking
- **Weighted scoring**: Configurable weights for different evaluation signals
- **EMA tracking**: Smooth score tracking across iterations
- **Intelligent halting**: Stop when tests pass + score threshold, no improvement, or max steps
- **Flexible candidate submission**: Support for multiple modes (files, patch, diff)
- **Safe execution**: Commands run in isolated directories with configurable timeouts
- **Python-specific**: Traceback parsing, pytest/unittest integration, Python linting
- **Data analysis focus**: Pandas/NumPy validation, data quality checks

## 🐍 Data Analysis Focus

This server is specifically designed for Python data analysis projects:

### Evaluation Signals

1. **Data Quality** (default weight: 0.3)
   - Schema validation
   - Missing value checks
   - Data type consistency
   - Pandas DataFrame validation
   - Custom data quality scripts

2. **Tests** (default weight: 0.4)
   - pytest integration
   - unittest support
   - JSON test reporters
   - Test coverage metrics

3. **Lint** (default weight: 0.1)
   - flake8 style checking
   - pylint code quality
   - mypy type checking
   - PEP 8 compliance

4. **Performance** (default weight: 0.2)
   - Runtime metrics
   - Memory profiling
   - Data processing benchmarks
   - Normalized performance scoring

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- pip for package management

### Install from source

```bash
git clone https://github.com/andreahaku/code_trm_python_mcp.git
cd code_trm_python_mcp
pip install -e .
```

### Development installation

```bash
pip install -e ".[dev]"
```

## 🚀 Usage

### As an MCP Server

Add to your MCP client configuration:

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

Or using the installed script:

```json
{
  "mcpServers": {
    "code-trm-python": {
      "command": "code-trm-python-mcp"
    }
  }
}
```
## 💬 Example Usage

Once configured as an MCP server in your LLM client, you can use natural language prompts:

### Starting a TRM Session

**Prompt:** *"Start a TRM session on my data analysis project at /Users/me/projects/data-pipeline. Use pytest for tests, flake8 and mypy for linting, and run data validation with `python scripts/validate_schemas.py`. Set max steps to 10 and stop when score reaches 0.95."*

This will invoke the `trm.start` tool to:
- Initialize session on the specified project
- Configure evaluation commands for data quality, tests, and lint
- Set halting policy (maxSteps=10, threshold=0.95)
- Return session ID for subsequent operations

### Iterative Improvement

**Prompt:** *"Submit a candidate that fixes the missing value handling in src/preprocessing.py. The issue is on lines 45-50 where we need to add fillna() for the 'age' column."*

This will:
- Apply the proposed changes to the file
- Run full evaluation pipeline (data quality, tests, lint, perf)
- Calculate weighted score
- Return feedback on what passed/failed
- Suggest whether to continue or halt

**Prompt:** *"What's the current state of the TRM session? Show me the score and whether we should stop iterating."*

Uses `trm.state` and `trm.halt` tools to:
- Display current step, EMA score, best score
- Show halting decision and reasons
- Provide improvement streak information

### Working with Files

**Prompt:** *"Read the contents of src/pipeline.py and data/schemas.py so I can see what needs to be fixed."*

Uses `trm.read` tool to:
- Fetch file contents from the repository
- Show metadata (line count, size, last modified)
- Provide context for making informed changes

**Prompt:** *"Show me lines 100-120 of src/analysis.py where the error occurred."*

Uses `trm.lines` tool to:
- Read specific line range with line numbers
- Provide focused context around error location
- Save tokens compared to reading entire file

### Getting Help

**Prompt:** *"The tests are failing with a NameError. Can you suggest a fix?"*

Uses `trm.fix` tool to:
- Analyze Python error traceback
- Identify the specific error (NameError: 'pandas' is not defined)
- Generate fix candidate (add `import pandas as pd`)
- Provide ready-to-apply candidate with rationale

**Prompt:** *"What improvements should I focus on based on the evaluation results?"*

Uses `trm.suggest` tool to:
- Analyze evaluation feedback
- Prioritize issues (critical → high → medium → low)
- Generate actionable suggestions
- Consider code quality, test coverage, performance

### Code Review

**Prompt:** *"Review the PR at https://github.com/user/repo/pull/123 and check for data validation issues, missing tests, and type safety problems."*

Uses `trm.review` tool to:
- Fetch PR diff from GitHub
- Analyze code changes
- Check for common issues (missing type hints, no error handling, etc.)
- Provide detailed comments with suggestions
- Give overall assessment (approved/needs-changes/comments)

### Checkpoints and Undo

**Prompt:** *"Save the current state as a checkpoint called 'before-refactoring'."*

Uses `trm.save` tool to save session state for later restoration.

**Prompt:** *"That last change made things worse. Undo it and restore the previous state."*

Uses `trm.undo` tool to:
- Restore files to previous state
- Roll back step counter
- Recalculate scores and EMA
- Show what was restored

### Example Complete Session

***Prompt:** "Let's improve the data validation in my pandas project. Start a TRM session at /path/to/project with these settings:
- Data validation: python scripts/check_schemas.py
- Tests: pytest --json tests/
- Lint: flake8 src/ && mypy src/
- Performance: python scripts/benchmark_pipeline.py
- Stop after 12 steps or when score reaches 0.97"

**Response:** ✅ Session started with ID abc-123...

**Prompt:** *"Read src/validators.py so I can see what needs to be improved."*

**Response:** [Shows file contents with 250 lines]

**Prompt:** *"Submit a candidate that adds schema validation for the 'transactions' DataFrame. It should check that required columns exist and have correct dtypes."*

**Response:**
- Step 1/12
- Score: 0.65
- Tests: 45/50 passed (5 failed)
- Data quality: ❌ Failed (schema mismatch detected)
- Feedback: Add validation for 'amount' column dtype

**Prompt:** *"Fix the schema validation based on that feedback."*

**Response:**
- Step 2/12
- Score: 0.82
- Tests: 48/50 passed (2 failed)
- Data quality: ✅ Passed
- Feedback: Remaining test failures in edge cases

**Prompt:** *"Keep iterating until tests pass or we should halt."*

[System continues iterating with LLM proposals...]

**Response:**
- Step 5/12
- Score: 0.96
- Tests: 50/50 passed ✅
- Data quality: ✅ Passed
- Should Halt: Yes - Success! Tests passing and score >= threshold

## 🛠️ Available Tools (16 Total)

### Core Tools

#### `trm.start` - Start Session

Initialize a TRM session on a local repository.

**Parameters:**
- `repo` (required): Absolute path to project
- `dataQual`: Data quality validation command
- `test`: Test command (e.g., "pytest --json")
- `lint`: Lint command (e.g., "flake8 src/")
- `bench`: Performance benchmark command
- `timeout`: Timeout per command (default: 120s)
- `weights`: Score weights (dataQual: 0.3, test: 0.4, lint: 0.1, perf: 0.2)
- `halt`: Halting policy (max, threshold, patience, min)
- `ema`: EMA smoothing factor (default: 0.9)
- `notes`: Optional initial reasoning notes

**Returns:** `sessionId`, `message`, config details

**Example:**
```python
session = await trm.start({
    "repo": "/path/to/project",
    "dataQual": "python scripts/validate_data.py",
    "test": "pytest --json tests/",
    "lint": "flake8 src/ && mypy src/",
    "bench": "python scripts/benchmark.py",
    "halt": {
        "max": 12,
        "threshold": 0.95,
        "patience": 3
    }
})
```

#### `trm.submit` - Submit Candidate

Apply candidate changes, run evaluation, return feedback.

**Parameters:**
- `sid` (required): Session ID
- `candidate` (required): One of these modes:
  - **files**: Complete file contents
  - **patch**: Unified diff format
  - **diff**: Per-file diffs
- `reason`: LLM reasoning notes

**Returns:** `step`, `score`, `emaScore`, `bestScore`, `tests`, `okDataQuality`, `okLint`, `shouldHalt`, `reasons`, `feedback`

**Example:**
```python
result = await trm.submit({
    "sid": session_id,
    "candidate": {
        "mode": "diff",
        "changes": [{
            "path": "src/analysis.py",
            "diff": "--- a/src/analysis.py\\n+++ b/src/analysis.py\\n..."
        }]
    },
    "reason": "Fix data validation logic"
})
```

#### `trm.read` - Get File Content

Read current file state with metadata.

**Parameters:**
- `sid` (required): Session ID
- `paths` (required): List of file paths

**Returns:** File contents with metadata (lineCount, sizeBytes, lastModified)

#### `trm.state` - Get State

Return current session state snapshot.

**Returns:** `sessionId`, `step`, `emaScore`, `bestScore`, `noImproveStreak`, `last`, `zNotes`

#### `trm.halt` - Should Halt

Check halting decision from latest evaluation.

**Returns:** `shouldHalt`, `reasons`

#### `trm.end` - End Session

Clean up and end session.

**Returns:** `ok`, `message`

### Enhancement Tools

#### `trm.validate` - Validate Candidate

Dry-run validation with detailed preview before applying changes.

**Parameters:** `sid`, `candidate`

**Returns:** `valid`, `errors`, `warnings`, `preview`

#### `trm.suggest` - Get Suggestions

Get AI-powered improvement suggestions based on evaluation results.

**Returns:** Top suggestions sorted by priority

### Checkpoint Tools

#### `trm.save` - Save Checkpoint

Save current session state as checkpoint.

**Parameters:** `sid`, `desc` (optional description)

#### `trm.restore` - Restore Checkpoint

Restore session from saved checkpoint.

**Parameters:** `sid`, `cid` (checkpoint ID)

#### `trm.list` - List Checkpoints

List all saved checkpoints for session.

**Parameters:** `sid`

### Advanced Tools

#### `trm.undo` - Undo Last Candidate

Quick undo with full state restoration.

**Returns:** `message`, `currentStep`, `score`, `emaScore`, `filesRestored`

#### `trm.lines` - Get File Lines

Read specific line range from a file with line numbers.

**Parameters:** `sid`, `file`, `start` (line number), `end` (line number)

**Returns:** Lines with formatted line numbers, total lineCount

#### `trm.fix` - Suggest Fix

AI-powered fix candidate generation based on Python error analysis.

**Supported errors:** NameError, ImportError, TypeError, AttributeError, SyntaxError

**Returns:** Array of suggestions with `priority`, `issue`, `candidateToFix`, `rationale`

#### `trm.reset` - Reset to Baseline

Reset repository to initial git commit state.

#### `trm.review` - PR Review

Perform detailed code review on pull requests from GitHub URLs or direct diffs.

**Parameters:**
- `url`: GitHub PR URL
- `diff`: Direct unified diff content
- `files`: Array of files with content
- `focus`: Optional array to filter review categories

**Focus categories:**
- `type-safety`: Detect missing type hints
- `logging`: Flag print statements
- `todos`: Identify TODO/FIXME comments
- `code-quality`: Magic numbers, long lines
- `error-handling`: Missing try-catch
- `testing`: Suggest adding tests
- `data-validation`: Missing data checks

## 📊 Score Calculation

Score is a weighted average in [0, 1]:

```
score = (w.dataQual * sDataQual + w.test * sTests + w.lint * sLint + w.perf * sPerf) / sumWeights

where:
  sDataQual = 1 if data quality checks pass, 0 otherwise
  sTests = passed / total (0 if tests fail to parse)
  sLint = 1 if lint succeeds, 0 otherwise
  sPerf = normalized performance score (best/current, lower runtime is better)
```

## 🛑 Halting Conditions

Iteration stops when:

1. **Success**: `step >= minSteps` AND all tests pass AND `score >= passThreshold`
2. **Plateau**: No improvement for `patience` consecutive steps
3. **Limit**: Reached `maxSteps`

## 🎯 Recommended Workflow

### 1. Start Session

```python
session = await trm.start({
    "repo": "/path/to/data-analysis-project",
    "dataQual": "python scripts/validate_schemas.py",
    "test": "pytest --json tests/",
    "lint": "flake8 src/ && mypy src/",
    "bench": "python scripts/benchmark_pipeline.py",
    "halt": {"max": 12, "threshold": 0.97, "patience": 3}
})
```

### 2. Iterative Improvement Loop

**Key principles:**
- Keep patches **small and focused** (one issue at a time)
- Use `reason` to maintain context across steps
- Trust the score/feedback signals for guidance

**Pattern:**
1. Get file content first
2. Submit candidate with rationale
3. If fails: use `trm.fix` or adjust approach
4. Repeat until `shouldHalt=true`

### 3. Example Iteration

```python
# 1. Get current files
files = await trm.read({"sid": session_id, "paths": ["src/pipeline.py"]})

# 2. Submit improvement
result = await trm.submit({
    "sid": session_id,
    "candidate": {
        "mode": "diff",
        "changes": [{
            "path": "src/pipeline.py",
            "diff": "..."
        }]
    },
    "reason": "Add data validation for missing values"
})

# 3. Check if should continue
if result["shouldHalt"]:
    print(f"Done! Final score: {result['score']}")
else:
    print(f"Continue - Step {result['step']}, Score: {result['score']}")
```

## 🐍 Python-Specific Features

### Error Parsing

Automatically parses Python tracebacks:
- NameError → suggests imports or variable definitions
- ImportError → suggests `pip install` commands
- TypeError → identifies argument mismatches
- AttributeError → detects incorrect attribute access
- SyntaxError → highlights syntax issues

### Test Framework Support

- **pytest**: JSON output parsing, fixture detection
- **unittest**: Standard output parsing, test discovery
- Coverage metrics integration

### Linting Integration

- **flake8**: Style checking
- **pylint**: Code quality analysis
- **mypy**: Type hint validation

### Data Analysis Validation

- Pandas DataFrame schema validation
- NumPy array shape/dtype checking
- Missing value detection
- Data type consistency validation

## 💡 Tips for Data Analysis Projects

1. **Set up data quality checks** that validate:
   - DataFrame schemas match expected structure
   - No unexpected missing values
   - Data types are correct
   - Value ranges are valid

2. **Use meaningful performance benchmarks**:
   - Time critical data processing pipelines
   - Measure memory usage for large datasets
   - Track improvement/regression across iterations

3. **Configure appropriate weights**:
   - Higher `test` weight for algorithm correctness
   - Higher `dataQual` weight for data pipeline reliability
   - Higher `perf` weight for optimization tasks

4. **Leverage pytest markers** for different test categories:
   - `@pytest.mark.unit` for fast unit tests
   - `@pytest.mark.integration` for data pipeline tests
   - `@pytest.mark.slow` for long-running tests

## 🏗️ Architecture

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

## 📝 Based On

This implementation is inspired by the **Test-time Recursive Memory (TRM)** approach from:
> "Recursive Introspection: Teaching Language Model Agents How to Self-Improve"
> (arXiv:2510.04871v1)

Key adaptations for Python data analysis:
- TRM's recursive refinement → Iterative code improvement with LLM proposals
- Latent reasoning (z) → Rationale/notes passed between iterations
- ACT halting → Configurable stopping policy based on score + improvement
- Deep supervision → Data quality/test/lint/perf signals as training-free feedback
- Python focus → Traceback parsing, pytest integration, data validation

## 📄 License

MIT

## 👨‍💻 Author

Andrea Salvatore (@andreahaku) with Claude (Anthropic)

## 🔗 Related Projects

- [llm-memory-mcp](https://github.com/andreahaku/llm_memory_mcp) - Persistent memory for LLM tools
- [code-analysis-context-python-mcp](https://github.com/andreahaku/code-analysis-context-python-mcp) - Code analysis for Python projects
- [code-trm-mcp](https://github.com/andreahaku/code_trm_mcp) - TypeScript/JavaScript version

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Status**: 🚧 **Beta** - Core functionality implemented, advanced features in progress

**Python Version**: 3.10+

**Focus**: Data Analysis & Scientific Computing (Pandas, NumPy, Scikit-learn)
