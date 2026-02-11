from smolagents import tool
import subprocess
from datetime import datetime

@tool
def git_commit(message: str) -> str:
    """
    Creates a git checkpoint (commit).
    Use this BEFORE making risky changes to code.
    
    Args:
        message: The commit message describing the checkpoint.
    """
    try:
        subprocess.run("git add .", shell=True, check=True)
        # Use --allow-empty in case nothing changed but we want a checkpoint mark
        cmd = f'git commit -m "[ARKA CHECKPOINT] {message}" --allow-empty'
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        return "✅ Checkpoint saved."
    except subprocess.CalledProcessError as e:
        return f"Error creating checkpoint: {str(e)}"

@tool
def git_reset_hard(commits_back: int = 1) -> str:
    """
    Undoes the last N commits (Hard Reset).
    DANGER: This deletes uncommitted changes and reverts history.
    
    Args:
        commits_back: Number of commits to rewind (default 1).
    """
    try:
        cmd = f"git reset --hard HEAD~{commits_back}"
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        return f"✅ Reverted last {commits_back} checkpoint(s)."
    except subprocess.CalledProcessError as e:
        return f"Error resetting git: {str(e)}"

@tool
def git_status() -> str:
    """
    Returns the current git status (changed files).
    """
    try:
        result = subprocess.run("git status --short", shell=True, capture_output=True, text=True)
        if not result.stdout.strip():
            return "No changes (Clean working tree)."
        return result.stdout
    except Exception as e:
        return str(e)
