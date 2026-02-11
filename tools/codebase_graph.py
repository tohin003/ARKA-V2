from smolagents import tool
import os
import ast
import networkx as nx
from typing import List, Dict

@tool
def generate_graph(directory: str = ".") -> str:
    """
    Analyzes the Python codebase in the given directory and generates a dependency/structure graph.
    Returns: A summary of the graph (nodes/edges count) and saves a 'codebase_graph.mermaid' file.
    
    Args:
        directory: Root directory to scan. Defaults to current directory.
    """
    g = nx.DiGraph()
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and "venv" not in root and ".git" not in root:
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, directory)
                
                try:
                    with open(path, "r") as f:
                        tree = ast.parse(f.read())
                        
                    # Add File Node
                    g.add_node(rel_path, type="file")
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            # Add Class Node
                            class_name = f"{rel_path}::{node.name}"
                            g.add_node(class_name, type="class")
                            g.add_edge(rel_path, class_name)
                            
                        elif isinstance(node, ast.FunctionDef):
                            # Add Function Node (if top level or inside class)
                            func_name = f"{rel_path}::{node.name}"
                            g.add_node(func_name, type="function")
                            g.add_edge(rel_path, func_name)
                            
                        elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                            # Minimal dependency tracking (naive)
                            pass 

                except Exception:
                    pass # Ignore parse errors

    # Export to Mermaid
    mermaid = ["graph TD"]
    for node in g.nodes:
        # Sanitize ID
        safe_id = node.replace("/", "_").replace(".", "_").replace(":", "_").replace("-", "_")
        label = node.split("::")[-1]
        mermaid.append(f"    {safe_id}[\"{label}\"]")
        
    for u, v in g.edges:
        u_safe = u.replace("/", "_").replace(".", "_").replace(":", "_").replace("-", "_")
        v_safe = v.replace("/", "_").replace(".", "_").replace(":", "_").replace("-", "_")
        mermaid.append(f"    {u_safe} --> {v_safe}")
        
    output_path = os.path.abspath("codebase_graph.mermaid")
    with open(output_path, "w") as f:
        f.write("\n".join(mermaid))
        
    return f"Graph generated with {len(g.nodes)} nodes and {len(g.edges)} edges. Saved to {output_path}."
