"""Parameter translator for short → long name mapping."""

from typing import Any, Dict


def translate_params(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translate short parameter names to long internal names.

    Args:
        tool_name: Tool name (e.g., "trm.start")
        args: Arguments with short names

    Returns:
        Arguments with long names
    """
    if tool_name == "trm.start":
        return _translate_start(args)
    elif tool_name == "trm.submit":
        return _translate_submit(args)
    elif tool_name == "trm.read":
        return _translate_read(args)
    elif tool_name in ["trm.state", "trm.halt", "trm.end", "trm.validate", "trm.suggest"]:
        return _translate_session_id(args)
    elif tool_name in ["trm.save", "trm.restore", "trm.list", "trm.reset", "trm.undo"]:
        return _translate_checkpoint(args, tool_name)
    elif tool_name == "trm.lines":
        return _translate_lines(args)
    elif tool_name == "trm.fix":
        return _translate_session_id(args)
    elif tool_name == "trm.review":
        return _translate_review(args)
    else:
        return args


def _translate_start(args: Dict[str, Any]) -> Dict[str, Any]:
    """Translate trm.start parameters."""
    translated = {
        "repo_path": args.get("repo"),
        "data_quality_cmd": args.get("dataQual"),
        "test_cmd": args.get("test"),
        "lint_cmd": args.get("lint"),
        "perf_cmd": args.get("bench"),
        "timeout_sec": args.get("timeout", 120),
        "z_notes": args.get("notes"),
        "ema_alpha": args.get("ema", 0.9),
    }

    # Translate weights
    if "weights" in args:
        w = args["weights"]
        translated["weights"] = {
            "data_quality": w.get("dataQual", 0.3),
            "test": w.get("test", 0.4),
            "lint": w.get("lint", 0.1),
            "perf": w.get("perf", 0.2),
        }

    # Translate halt policy
    if "halt" in args:
        h = args["halt"]
        translated["halt"] = {
            "max_steps": h.get("max", 12),
            "pass_threshold": h.get("threshold", 0.95),
            "patience_no_improve": h.get("patience", 3),
            "min_steps": h.get("min", 1),
        }

    # Remove None values
    return {k: v for k, v in translated.items() if v is not None}


def _translate_submit(args: Dict[str, Any]) -> Dict[str, Any]:
    """Translate trm.submit parameters."""
    return {
        "session_id": args.get("sid"),
        "candidate": args.get("candidate"),
        "rationale": args.get("reason"),
    }


def _translate_read(args: Dict[str, Any]) -> Dict[str, Any]:
    """Translate trm.read parameters."""
    return {
        "session_id": args.get("sid"),
        "paths": args.get("paths", []),
    }


def _translate_session_id(args: Dict[str, Any]) -> Dict[str, Any]:
    """Translate simple session_id parameter."""
    return {
        "session_id": args.get("sid"),
    }


def _translate_checkpoint(args: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
    """Translate checkpoint-related parameters."""
    result = {"session_id": args.get("sid")}

    if tool_name == "trm.save":
        result["description"] = args.get("desc")
    elif tool_name == "trm.restore":
        result["checkpoint_id"] = args.get("cid")

    return result


def _translate_lines(args: Dict[str, Any]) -> Dict[str, Any]:
    """Translate trm.lines parameters."""
    return {
        "session_id": args.get("sid"),
        "file": args.get("file"),
        "start_line": args.get("start"),
        "end_line": args.get("end"),
    }


def _translate_review(args: Dict[str, Any]) -> Dict[str, Any]:
    """Translate trm.review parameters."""
    return {
        "pr_url": args.get("url"),
        "diff": args.get("diff"),
        "files": args.get("files"),
        "focus": args.get("focus"),
    }
