from smolagents import tool
import os
import glob
from typing import List, Optional

@tool
def read_file(path: str, line_numbers: bool = True) -> str:
    """
    Reads a file and returns its content. Supports .txt, .py, .md, .json, .pdf, etc.
    
    Args:
        path: Absolute path to the file.
        line_numbers: Whether to add line numbers to the output (default True).
    """
    if not os.path.exists(path):
        return f"Error: File not found at {path}"
    
    try:
        # Handle PDF
        if path.strip().lower().endswith(".pdf"):
            import pypdf
            reader = pypdf.PdfReader(path)
            text = []
            for page in reader.pages:
                text.append(page.extract_text())
            return "\n".join(text)

        # Handle Text
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if line_numbers:
            return "\n".join([f"{i+1:4d} | {line.rstrip()}" for i, line in enumerate(lines)])
        else:
            return "".join(lines)
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def write_file(path: str, content: str) -> str:
    """
    Writes content to a file. Overwrites if exists.
    
    Args:
        path: Absolute path to the file.
        content: The content to write.
    """
    try:
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@tool
def grep(pattern: str, path: str = ".") -> str:
    """
    Searches for a pattern in files within a directory (recursive).
    
    Args:
        pattern: The text to search for.
        path: The directory or file path to search in (default: current dir).
    """
    # We use grep via subprocess for speed and robustness
    import subprocess
    cmd = f"grep -rn '{pattern}' '{path}' | head -n 200" # Limit results
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if not result.stdout:
            return "No matches found."
        return result.stdout
    except Exception as e:
        return f"Error running grep: {str(e)}"
