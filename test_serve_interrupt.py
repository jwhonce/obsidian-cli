#!/usr/bin/env python3
"""Test script to check serve command interruption behavior."""

import signal
import subprocess
import sys
import time


def test_serve_interrupt():
    """Test interrupting the serve command to check for stack traces."""
    print("Testing serve command interruption...")

    # Start the serve command
    cmd = [sys.executable, "-m", "obsidian_cli.main", "--vault", "test_vault", "--verbose", "serve"]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/Users/honce/Projects/obsidian/obsidian-cli",
    )

    # Let it start up
    time.sleep(2)

    # Send interrupt
    process.send_signal(signal.SIGINT)

    # Wait for it to finish
    stdout, stderr = process.communicate(timeout=5)

    print("Return code:", process.returncode)
    print("STDOUT:")
    print(stdout)
    print("STDERR:")
    print(stderr)

    # Check for stack trace indicators
    stack_trace_indicators = ["Traceback", 'File "', "line ", "^C"]
    has_stack_trace = any(indicator in stderr for indicator in stack_trace_indicators)

    print(f"Has stack trace: {has_stack_trace}")

    return not has_stack_trace


if __name__ == "__main__":
    test_serve_interrupt()
