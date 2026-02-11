from smolagents import tool
import json
import os
from typing import List, Dict
import structlog
from rich.console import Console
from rich.table import Table

logger = structlog.get_logger()
TODO_FILE = os.path.expanduser("~/.arka/todos.json")

class TodoManager:
    def __init__(self):
        self.todos: List[Dict] = []
        self._load()

    def _load(self):
        if os.path.exists(TODO_FILE):
             try:
                 with open(TODO_FILE, 'r') as f:
                     self.todos = json.load(f)
             except:
                 self.todos = []
    
    def _save(self):
        os.makedirs(os.path.dirname(TODO_FILE), exist_ok=True)
        with open(TODO_FILE, 'w') as f:
            json.dump(self.todos, f)

    def add(self, task: str):
        self.todos.append({"task": task, "done": False})
        self._save()
        return f"Added task: {task}"

    def list_tasks(self) -> str:
        if not self.todos:
            return "No tasks."
        
        # Use Rich for pretty printing to console, but return text for LLM
        table = Table(title="Current Tasks")
        table.add_column("Status", style="cyan", no_wrap=True)
        table.add_column("Task", style="white")

        text_output = []
        for i, t in enumerate(self.todos):
            status = "✅" if t['done'] else "[ ]"
            table.add_row(status, f"{i}. {t['task']}")
            text_output.append(f"{i}. [{status}] {t['task']}")
        
        console = Console()
        console.print(table)
        
        return "\n".join(text_output)

    def complete(self, index: int):
        if 0 <= index < len(self.todos):
            self.todos[index]['done'] = True
            self._save()
            return f"Marked task {index} as done."
        return "Invalid task index."

manager = TodoManager()

@tool
def todo_add(task: str) -> str:
    """
    Adds a task to the todo list.
    
    Args:
        task: The description of the task to be added.
    """
    return manager.add(task)

@tool
def todo_list() -> str:
    """
    Lists all current tasks.
    """
    return manager.list_tasks()

@tool
def todo_complete(index: int) -> str:
    """
    Mark a task as complete by its index.
    
    Args:
        index: The index of the task to complete (0-based).
    """
    return manager.complete(index)
