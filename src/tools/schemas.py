"""MCP tool schemas for TRM Python server."""

from mcp.types import Tool

# Token-optimized tool schemas for Python data analysis TRM
tools: list[Tool] = [
    Tool(
        name="trm.start",
        description="Init session with eval commands & halt policy.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "dataQual": {"type": "string"},
                "test": {"type": "string"},
                "lint": {"type": "string"},
                "bench": {"type": "string"},
                "timeout": {"type": "number", "default": 120},
                "weights": {
                    "type": "object",
                    "properties": {
                        "dataQual": {"type": "number", "default": 0.3},
                        "test": {"type": "number", "default": 0.4},
                        "lint": {"type": "number", "default": 0.1},
                        "perf": {"type": "number", "default": 0.2},
                    },
                },
                "halt": {
                    "type": "object",
                    "properties": {
                        "max": {"type": "number", "default": 12},
                        "threshold": {"type": "number", "default": 0.95},
                        "patience": {"type": "number", "default": 3},
                        "min": {"type": "number", "default": 1},
                    },
                    "required": ["max", "threshold", "patience"],
                },
                "ema": {"type": "number", "default": 0.9},
                "notes": {"type": "string"},
            },
            "required": ["repo", "halt"],
        },
    ),
    Tool(
        name="trm.submit",
        description="Apply changes & eval. Prefer diff/patch modes.",
        inputSchema={
            "type": "object",
            "properties": {
                "sid": {"type": "string"},
                "candidate": {
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {
                                "mode": {"const": "diff"},
                                "changes": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "path": {"type": "string"},
                                            "diff": {"type": "string"},
                                        },
                                        "required": ["path", "diff"],
                                    },
                                },
                            },
                            "required": ["mode", "changes"],
                        },
                        {
                            "type": "object",
                            "properties": {
                                "mode": {"const": "patch"},
                                "patch": {"type": "string"},
                            },
                            "required": ["mode", "patch"],
                        },
                        {
                            "type": "object",
                            "properties": {
                                "mode": {"const": "files"},
                                "files": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "path": {"type": "string"},
                                            "content": {"type": "string"},
                                        },
                                        "required": ["path", "content"],
                                    },
                                },
                            },
                            "required": ["mode", "files"],
                        },
                    ],
                },
                "reason": {"type": "string"},
            },
            "required": ["sid", "candidate"],
        },
    ),
    Tool(
        name="trm.read",
        description="Read file contents.",
        inputSchema={
            "type": "object",
            "properties": {
                "sid": {"type": "string"},
                "paths": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["sid", "paths"],
        },
    ),
    Tool(
        name="trm.state",
        description="Get session state.",
        inputSchema={
            "type": "object",
            "properties": {"sid": {"type": "string"}},
            "required": ["sid"],
        },
    ),
    Tool(
        name="trm.halt",
        description="Get halt decision.",
        inputSchema={
            "type": "object",
            "properties": {"sid": {"type": "string"}},
            "required": ["sid"],
        },
    ),
    Tool(
        name="trm.end",
        description="End session.",
        inputSchema={
            "type": "object",
            "properties": {"sid": {"type": "string"}},
            "required": ["sid"],
        },
    ),
    Tool(
        name="trm.validate",
        description="Validate changes (dry-run).",
        inputSchema={
            "type": "object",
            "properties": {
                "sid": {"type": "string"},
                "candidate": {"type": "object"},
            },
            "required": ["sid", "candidate"],
        },
    ),
    Tool(
        name="trm.suggest",
        description="Get AI suggestions.",
        inputSchema={
            "type": "object",
            "properties": {"sid": {"type": "string"}},
            "required": ["sid"],
        },
    ),
    Tool(
        name="trm.save",
        description="Save checkpoint.",
        inputSchema={
            "type": "object",
            "properties": {
                "sid": {"type": "string"},
                "desc": {"type": "string"},
            },
            "required": ["sid"],
        },
    ),
    Tool(
        name="trm.restore",
        description="Restore checkpoint.",
        inputSchema={
            "type": "object",
            "properties": {
                "sid": {"type": "string"},
                "cid": {"type": "string"},
            },
            "required": ["sid", "cid"],
        },
    ),
    Tool(
        name="trm.list",
        description="List checkpoints.",
        inputSchema={
            "type": "object",
            "properties": {"sid": {"type": "string"}},
            "required": ["sid"],
        },
    ),
    Tool(
        name="trm.reset",
        description="Reset to baseline.",
        inputSchema={
            "type": "object",
            "properties": {"sid": {"type": "string"}},
            "required": ["sid"],
        },
    ),
    Tool(
        name="trm.undo",
        description="Undo last candidate.",
        inputSchema={
            "type": "object",
            "properties": {"sid": {"type": "string"}},
            "required": ["sid"],
        },
    ),
    Tool(
        name="trm.lines",
        description="Read line range.",
        inputSchema={
            "type": "object",
            "properties": {
                "sid": {"type": "string"},
                "file": {"type": "string"},
                "start": {"type": "number"},
                "end": {"type": "number"},
            },
            "required": ["sid", "file", "start", "end"],
        },
    ),
    Tool(
        name="trm.fix",
        description="Generate fix candidates.",
        inputSchema={
            "type": "object",
            "properties": {"sid": {"type": "string"}},
            "required": ["sid"],
        },
    ),
    Tool(
        name="trm.review",
        description="Detailed PR review from URL or diff.",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "diff": {"type": "string"},
                "files": {"type": "array"},
                "focus": {"type": "array", "items": {"type": "string"}},
            },
        },
    ),
]
