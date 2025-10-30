"""Command execution utilities."""

import asyncio
import subprocess
from pathlib import Path
from typing import Optional
from ..types import CommandResult


async def run_command(
    cmd: str,
    cwd: str | Path,
    timeout_sec: int = 120,
    env: Optional[dict] = None,
) -> CommandResult:
    """
    Run shell command asynchronously with timeout.

    Args:
        cmd: Command string to execute
        cwd: Working directory
        timeout_sec: Timeout in seconds
        env: Optional environment variables

    Returns:
        CommandResult with stdout, stderr, exit code
    """
    cwd_path = Path(cwd).resolve()

    if not cwd_path.exists():
        return CommandResult(
            ok=False,
            stdout="",
            stderr=f"Directory does not exist: {cwd_path}",
            exit_code=1,
        )

    try:
        # Run command with timeout
        process = await asyncio.create_subprocess_shell(
            cmd,
            cwd=str(cwd_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_sec
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            exit_code = process.returncode

        except asyncio.TimeoutError:
            # Kill process on timeout
            try:
                process.kill()
                await process.wait()
            except:
                pass

            return CommandResult(
                ok=False,
                stdout="",
                stderr=f"Command timed out after {timeout_sec}s",
                exit_code=-1,
            )

        return CommandResult(
            ok=(exit_code == 0),
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
        )

    except Exception as e:
        return CommandResult(
            ok=False,
            stdout="",
            stderr=f"Command execution failed: {str(e)}",
            exit_code=-1,
        )


def check_command_available(cmd: str) -> bool:
    """
    Check if a command is available in the system.

    Args:
        cmd: Command name (e.g., "pytest", "flake8")

    Returns:
        True if command is available
    """
    try:
        # Extract just the command name (before first space/argument)
        cmd_name = cmd.split()[0] if " " in cmd else cmd

        result = subprocess.run(
            ["which", cmd_name],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False
