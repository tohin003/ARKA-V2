import subprocess
import shlex
from smolagents import tool
from typing import Optional

TRUNCATION_LIMIT = 2000
TRUNCATION_MESSAGE = "\n... [Output truncated. Total lines: {total}. Use 'read_last_lines' or 'grep' to see more.]"

@tool
def run_terminal(command: str, read_all: bool = False) -> str:
    """
    Executes a command in the terminal and returns the output.
    
    Args:
        command: The shell command to execute.
        read_all: If True, ignores the 2000-line limit (Use with caution!).
    """
    try:
        # We use a large timeout to allow builds, but not infinite
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300 # 5 minutes max per command
        )
        
        # Combine stdout and stderr
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"
            
        # Truncation Logic
        lines = output.splitlines()
        total_lines = len(lines)
        
        if not read_all and total_lines > TRUNCATION_LIMIT:
            # Head + Tail Strategy: Keep first 1500 and last 500
            head = lines[:1500]
            tail = lines[-500:]
            truncated_output = "\n".join(head)
            truncated_output += TRUNCATION_MESSAGE.format(total=total_lines)
            truncated_output += "\n" + "\n".join(tail)
            return truncated_output
            
        return output

    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 300 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"
