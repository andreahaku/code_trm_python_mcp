#!/usr/bin/env python3
"""TRM Python MCP Server - Main entry point."""

import asyncio
import json
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from .tools.schemas import tools
from .tools.param_translator import translate_params
from .shared.sessions import (
    create_session,
    get_session,
    delete_session,
)
from .tools.handlers.lib.evaluation import run_evaluation, run_preflight_checks
from .types import SessionMode, WeightsConfig, HaltConfig


async def handle_tool_call(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle MCP tool calls.

    Args:
        name: Tool name
        arguments: Tool arguments (short names)

    Returns:
        List of TextContent responses
    """
    # Translate short parameter names to long names
    args = translate_params(name, arguments)

    try:
        if name == "trm.start":
            return await handle_start_session(args)
        elif name == "trm.submit":
            return await handle_submit_candidate(args)
        elif name == "trm.read":
            return await handle_get_file_content(args)
        elif name == "trm.state":
            return await handle_get_state(args)
        elif name == "trm.halt":
            return await handle_should_halt(args)
        elif name == "trm.end":
            return await handle_end_session(args)
        elif name == "trm.validate":
            return await handle_validate_candidate(args)
        elif name == "trm.suggest":
            return await handle_get_suggestions(args)
        elif name in ["trm.save", "trm.restore", "trm.list"]:
            return await handle_checkpoint(name, args)
        elif name == "trm.reset":
            return await handle_reset_baseline(args)
        elif name == "trm.undo":
            return await handle_undo_last_candidate(args)
        elif name == "trm.lines":
            return await handle_get_file_lines(args)
        elif name == "trm.fix":
            return await handle_suggest_fix(args)
        elif name == "trm.review":
            return await handle_review_pr(args)
        else:
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2),
                )
            ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2),
            )
        ]


async def handle_start_session(args: dict) -> list[TextContent]:
    """Handle trm.start - Initialize session."""
    # Create weights config
    weights = None
    if "weights" in args:
        weights = WeightsConfig(**args["weights"])

    # Create halt config
    halt = HaltConfig(**args["halt"])

    # Create session
    session = create_session(
        repo_path=args["repo_path"],
        data_quality_cmd=args.get("data_quality_cmd"),
        test_cmd=args.get("test_cmd"),
        lint_cmd=args.get("lint_cmd"),
        perf_cmd=args.get("perf_cmd"),
        timeout_sec=args.get("timeout_sec", 120),
        weights=weights,
        halt=halt.__dict__,
        ema_alpha=args.get("ema_alpha", 0.9),
        z_notes=args.get("z_notes"),
        mode=SessionMode.CUMULATIVE,
    )

    response = {
        "sessionId": session.id,
        "message": "TRM session initialized",
        "config": {
            "repoPath": session.cfg.repo_path,
            "haltPolicy": {
                "maxSteps": session.cfg.halt.max_steps,
                "passThreshold": session.cfg.halt.pass_threshold,
            },
        },
    }

    # Run preflight checks if requested
    if args.get("preflight"):
        preflight = await run_preflight_checks(session)
        response["preflight"] = preflight

    return [TextContent(type="text", text=json.dumps(response, indent=2))]


async def handle_submit_candidate(args: dict) -> list[TextContent]:
    """Handle trm.submit - Submit and evaluate candidate."""
    session = get_session(args["session_id"])
    if not session:
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": "Session not found"}, indent=2),
            )
        ]

    # For now, simplified implementation
    # In full version, this would apply the candidate changes to files
    # then run the evaluation

    # Run evaluation
    eval_result = await run_evaluation(session)

    response = {
        "step": eval_result.step,
        "score": eval_result.score,
        "emaScore": eval_result.ema_score,
        "bestScore": session.best_score,
        "feedback": eval_result.feedback,
        "shouldHalt": eval_result.should_halt,
        "reasons": eval_result.reasons,
        "tests": {
            "passed": eval_result.tests.passed if eval_result.tests else 0,
            "failed": eval_result.tests.failed if eval_result.tests else 0,
            "total": eval_result.tests.total if eval_result.tests else 0,
        }
        if eval_result.tests
        else None,
        "okDataQuality": eval_result.ok_data_quality,
        "okLint": eval_result.ok_lint,
    }

    return [TextContent(type="text", text=json.dumps(response, indent=2))]


async def handle_get_file_content(args: dict) -> list[TextContent]:
    """Handle trm.read - Get file contents."""
    session = get_session(args["session_id"])
    if not session:
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": "Session not found"}, indent=2),
            )
        ]

    from pathlib import Path

    repo_path = Path(session.cfg.repo_path)
    files = {}

    for path_str in args["paths"]:
        file_path = repo_path / path_str
        if file_path.exists() and file_path.is_file():
            try:
                content = file_path.read_text(encoding="utf-8")
                stat = file_path.stat()
                files[path_str] = {
                    "content": content,
                    "metadata": {
                        "lineCount": len(content.splitlines()),
                        "sizeBytes": stat.st_size,
                        "lastModified": stat.st_mtime,
                    },
                }
            except Exception as e:
                files[path_str] = {"error": str(e)}
        else:
            files[path_str] = {"error": "File not found"}

    return [TextContent(type="text", text=json.dumps({"files": files}, indent=2))]


async def handle_get_state(args: dict) -> list[TextContent]:
    """Handle trm.state - Get session state."""
    session = get_session(args["session_id"])
    if not session:
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": "Session not found"}, indent=2),
            )
        ]

    response = {
        "sessionId": session.id,
        "step": session.step,
        "emaScore": session.ema_score,
        "bestScore": session.best_score,
        "noImproveStreak": session.no_improve_streak,
        "last": session.history[-1].__dict__ if session.history else None,
        "zNotes": session.z_notes,
    }

    return [TextContent(type="text", text=json.dumps(response, indent=2))]


async def handle_should_halt(args: dict) -> list[TextContent]:
    """Handle trm.halt - Check halting decision."""
    session = get_session(args["session_id"])
    if not session:
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": "Session not found"}, indent=2),
            )
        ]

    last_eval = session.history[-1] if session.history else None
    if not last_eval:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"shouldHalt": False, "reasons": ["No evaluations yet"]}, indent=2
                ),
            )
        ]

    response = {
        "shouldHalt": last_eval.should_halt,
        "reasons": last_eval.reasons,
    }

    return [TextContent(type="text", text=json.dumps(response, indent=2))]


async def handle_end_session(args: dict) -> list[TextContent]:
    """Handle trm.end - End session."""
    deleted = delete_session(args["session_id"])
    response = {"ok": deleted, "message": "Session ended" if deleted else "Session not found"}
    return [TextContent(type="text", text=json.dumps(response, indent=2))]


# Placeholder handlers for remaining tools
async def handle_validate_candidate(args: dict) -> list[TextContent]:
    """Handle trm.validate - Validate candidate (placeholder)."""
    return [
        TextContent(
            type="text",
            text=json.dumps(
                {"valid": True, "errors": [], "warnings": [], "message": "Validation not implemented yet"},
                indent=2,
            ),
        )
    ]


async def handle_get_suggestions(args: dict) -> list[TextContent]:
    """Handle trm.suggest - Get suggestions (placeholder)."""
    return [TextContent(type="text", text=json.dumps({"suggestions": []}, indent=2))]


async def handle_checkpoint(name: str, args: dict) -> list[TextContent]:
    """Handle checkpoint operations (placeholder)."""
    return [
        TextContent(type="text", text=json.dumps({"message": f"{name} not implemented yet"}, indent=2))
    ]


async def handle_reset_baseline(args: dict) -> list[TextContent]:
    """Handle trm.reset (placeholder)."""
    return [TextContent(type="text", text=json.dumps({"message": "Reset not implemented yet"}, indent=2))]


async def handle_undo_last_candidate(args: dict) -> list[TextContent]:
    """Handle trm.undo (placeholder)."""
    return [TextContent(type="text", text=json.dumps({"message": "Undo not implemented yet"}, indent=2))]


async def handle_get_file_lines(args: dict) -> list[TextContent]:
    """Handle trm.lines (placeholder)."""
    return [TextContent(type="text", text=json.dumps({"lines": [], "message": "Not implemented yet"}, indent=2))]


async def handle_suggest_fix(args: dict) -> list[TextContent]:
    """Handle trm.fix (placeholder)."""
    return [TextContent(type="text", text=json.dumps({"suggestions": []}, indent=2))]


async def handle_review_pr(args: dict) -> list[TextContent]:
    """Handle trm.review (placeholder)."""
    return [
        TextContent(
            type="text",
            text=json.dumps(
                {"summary": {}, "comments": [], "message": "PR review not implemented yet"}, indent=2
            ),
        )
    ]


async def main():
    """Main entry point for MCP server."""
    server = Server("code-trm-python-mcp")

    @server.list_tools()
    async def list_tools():
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        result = await handle_tool_call(name, arguments)
        return result

    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
