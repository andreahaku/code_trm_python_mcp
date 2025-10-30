#!/usr/bin/env python3
"""Test script to demonstrate TRM Python MCP server functionality."""

import asyncio
import json
from src.server import handle_tool_call


async def test_basic_workflow():
    """Test basic TRM workflow."""
    print("=" * 80)
    print("TRM PYTHON MCP SERVER - BASIC WORKFLOW TEST")
    print("=" * 80)
    print()

    # Test 1: Start session
    print("TEST 1: Starting TRM Session")
    print("-" * 80)

    start_result = await handle_tool_call(
        "trm.start",
        {
            "repo": ".",
            "test": "pytest tests/ --json",
            "lint": "flake8 src/",
            "halt": {
                "max": 5,
                "threshold": 0.9,
                "patience": 2,
            },
        },
    )

    start_data = json.loads(start_result[0].text)
    print(json.dumps(start_data, indent=2))
    session_id = start_data.get("sessionId")
    print(f"\\n✅ Session created: {session_id}")
    print()

    # Test 2: Get session state
    print("TEST 2: Getting Session State")
    print("-" * 80)

    state_result = await handle_tool_call("trm.state", {"sid": session_id})
    state_data = json.loads(state_result[0].text)
    print(json.dumps(state_data, indent=2))
    print()

    # Test 3: Read file content
    print("TEST 3: Reading File Content")
    print("-" * 80)

    read_result = await handle_tool_call(
        "trm.read",
        {
            "sid": session_id,
            "paths": ["README.md", "pyproject.toml"],
        },
    )

    read_data = json.loads(read_result[0].text)
    for path, file_data in read_data.get("files", {}).items():
        if "metadata" in file_data:
            metadata = file_data["metadata"]
            print(f"✅ {path}:")
            print(f"   Lines: {metadata['lineCount']}")
            print(f"   Size: {metadata['sizeBytes']} bytes")
        else:
            print(f"❌ {path}: {file_data.get('error', 'Unknown error')}")
    print()

    # Test 4: Submit a candidate (no-op for now)
    print("TEST 4: Submitting Candidate (evaluation only)")
    print("-" * 80)

    submit_result = await handle_tool_call(
        "trm.submit",
        {
            "sid": session_id,
            "candidate": {
                "mode": "files",
                "files": [{"path": "test.py", "content": "# Test file\\nprint('hello')\\n"}],
            },
            "reason": "Test submission",
        },
    )

    submit_data = json.loads(submit_result[0].text)
    print(f"Step: {submit_data.get('step')}")
    print(f"Score: {submit_data.get('score')}")
    print(f"EMA Score: {submit_data.get('emaScore')}")
    print(f"Best Score: {submit_data.get('bestScore')}")
    print(f"Should Halt: {submit_data.get('shouldHalt')}")
    print(f"\\nFeedback:")
    for feedback in submit_data.get("feedback", []):
        print(f"  {feedback}")
    print()

    # Test 5: Check halting decision
    print("TEST 5: Checking Halting Decision")
    print("-" * 80)

    halt_result = await handle_tool_call("trm.halt", {"sid": session_id})
    halt_data = json.loads(halt_result[0].text)
    print(f"Should Halt: {halt_data.get('shouldHalt')}")
    print(f"Reasons:")
    for reason in halt_data.get("reasons", []):
        print(f"  {reason}")
    print()

    # Test 6: End session
    print("TEST 6: Ending Session")
    print("-" * 80)

    end_result = await handle_tool_call("trm.end", {"sid": session_id})
    end_data = json.loads(end_result[0].text)
    print(json.dumps(end_data, indent=2))
    print()

    print("=" * 80)
    print("ALL TESTS COMPLETED!")
    print("=" * 80)
    print()

    print("📝 NOTES:")
    print("  - This is a basic test demonstrating the MCP tool interface")
    print("  - File patching is not yet implemented (no actual changes applied)")
    print("  - Evaluation pipeline runs but may not have configured commands")
    print("  - For full functionality, configure data quality, test, lint, and perf commands")
    print()


async def test_error_parser():
    """Test Python error parser."""
    print("=" * 80)
    print("TESTING PYTHON ERROR PARSER")
    print("=" * 80)
    print()

    from src.utils.py_error_parser import parse_python_traceback, format_error_for_llm

    # Sample Python traceback
    sample_traceback = '''Traceback (most recent call last):
  File "/path/to/script.py", line 42, in main
    result = process_data(df)
  File "/path/to/lib.py", line 123, in process_data
    return data.mean()
AttributeError: 'NoneType' object has no attribute 'mean'
'''

    errors = parse_python_traceback(sample_traceback)
    print(f"Parsed {len(errors)} error(s):")
    print()

    for error in errors:
        print(format_error_for_llm(error))
        print()

    print("=" * 80)
    print()


async def main():
    """Run all tests."""
    try:
        # Test basic workflow
        await test_basic_workflow()

        # Test error parser
        await test_error_parser()

        print("\\n✅ All tests passed successfully!")
        print()
        print("🚀 Next steps:")
        print("  1. Configure your MCP client to use this server")
        print("  2. Point it to a real Python data analysis project")
        print("  3. Set up data quality, test, lint, and performance commands")
        print("  4. Start iterating with the LLM!")
        print()

    except Exception as e:
        print(f"\\n❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
