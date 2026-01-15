"""
Tool Discovery and Search Utilities

This module provides utilities for discovering available tools
and searching for relevant tools based on keywords or functionality.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Any


def list_available_tools(tools_dir: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """
    Discover all available tools by scanning the tools directory.

    Args:
        tools_dir: Path to tools directory (default: backend/tools/)

    Returns:
        Dictionary mapping tool names to their metadata:
        {
            'tool_name': {
                'module_path': str,
                'function_name': str,
                'description': str,
                'parameters': dict,
                'file_path': str
            }
        }
    """
    if tools_dir is None:
        tools_dir = Path(__file__).parent

    tools = {}

    # Skip __pycache__ and private files
    for plugin_dir in tools_dir.iterdir():
        if not plugin_dir.is_dir() or plugin_dir.name.startswith('_'):
            continue

        # Look for Python files in plugin directory
        for tool_file in plugin_dir.glob('*.py'):
            if tool_file.name.startswith('_'):
                continue

            try:
                tool_info = _extract_tool_info(tool_file)
                if tool_info:
                    tool_key = f"{plugin_dir.name}_{tool_file.stem}"
                    tools[tool_key] = tool_info
            except Exception as e:
                # Log but continue scanning
                print(f"Warning: Could not extract info from {tool_file}: {e}")

    return tools


def _extract_tool_info(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract tool metadata from a Python file.

    Parses the file to find async functions and their docstrings.
    """
    try:
        import ast
        source = file_path.read_text(encoding='utf-8')

        # Try to parse - if it fails due to encoding issues, use a simpler approach
        try:
            tree = ast.parse(source)
        except SyntaxError:
            # Fallback: scan for async functions using regex
            return _extract_tool_info_fallback(file_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                func_name = node.name

                # Get docstring
                docstring = ast.get_docstring(node) or ""

                # Extract parameters
                parameters = {}
                for arg in node.args.args:
                    if arg.arg != 'self':
                        param_name = arg.arg
                        param_annotation = ast.unparse(arg.annotation) if arg.annotation else 'Any'
                        parameters[param_name] = param_annotation

                return {
                    'module_path': f"{file_path.parent.name}.{file_path.stem}",
                    'function_name': func_name,
                    'description': docstring.split('\n\n')[0] if docstring else '',
                    'full_docstring': docstring,
                    'parameters': parameters,
                    'file_path': str(file_path)
                }
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

    return None


def _extract_tool_info_fallback(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Fallback method to extract tool info using regex when AST parsing fails.

    This handles files with special characters or encoding issues.
    """
    try:
        source = file_path.read_text(encoding='utf-8')

        # Find async function definitions
        import re
        func_pattern = r'async\s+def\s+(\w+)\s*\(([^)]*)\)\s*->[^:]+:'
        match = re.search(func_pattern, source)

        if not match:
            return None

        func_name = match.group(1)
        params_str = match.group(2)

        # Parse parameters
        parameters = {}
        if params_str.strip():
            for param in params_str.split(','):
                param = param.strip()
                if param and '=' not in param:
                    param_name = param.split(':')[0].strip()
                    parameters[param_name] = 'str'

        # Extract description (first line after docstring start)
        desc_match = re.search(r'"""?\s*([^\n]+)', source)
        description = desc_match.group(1).strip() if desc_match else ''

        return {
            'module_path': f"{file_path.parent.name}.{file_path.stem}",
            'function_name': func_name,
            'description': description[:200] if description else '',
            'full_docstring': description,
            'parameters': parameters,
            'file_path': str(file_path)
        }
    except Exception as e:
        print(f"Error in fallback parsing {file_path}: {e}")
        return None


def search_tools(
    query: str,
    tools_dir: Optional[Path] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Search for tools matching a query string.

    Args:
        query: Search query (keywords, description)
        tools_dir: Path to tools directory
        limit: Maximum number of results to return

    Returns:
        List of matching tool metadata dicts, sorted by relevance
    """
    all_tools = list_available_tools(tools_dir)

    # Simple keyword matching
    query_lower = query.lower()
    scores = {}

    for tool_key, tool_info in all_tools.items():
        score = 0

        # Match in function name
        if query_lower in tool_info['function_name'].lower():
            score += 10

        # Match in description
        description = tool_info['description'].lower()
        if query_lower in description:
            score += 5

        # Match in module path
        if query_lower in tool_info['module_path'].lower():
            score += 3

        # Match in parameter names
        for param_name in tool_info['parameters'].keys():
            if query_lower in param_name.lower():
                score += 2

        if score > 0:
            scores[tool_key] = score

    # Sort by score
    sorted_tools = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Return top N
    results = []
    for tool_key, score in sorted_tools[:limit]:
        tool_info = all_tools[tool_key].copy()
        tool_info['relevance_score'] = score
        results.append(tool_info)

    return results


def get_tool_by_name(tool_name: str, tools_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Get tool metadata by exact name match.

    Args:
        tool_name: Exact tool name to find (e.g., 'tavily_search_search')
        tools_dir: Path to tools directory

    Returns:
        Tool metadata dict or None if not found
    """
    all_tools = list_available_tools(tools_dir)
    return all_tools.get(tool_name)


def import_tool_function(tool_name: str, tools_dir: Optional[Path] = None):
    """
    Dynamically import a tool function by name.

    Args:
        tool_name: Tool name (e.g., 'tavily_search_search')
        tools_dir: Path to tools directory

    Returns:
        The imported function object

    Raises:
        ImportError: If tool cannot be imported
    """
    tool_info = get_tool_by_name(tool_name, tools_dir)
    if not tool_info:
        raise ImportError(f"Tool '{tool_name}' not found")

    module_path = tool_info['module_path']
    function_name = tool_info['function_name']

    # Build absolute module path
    if tools_dir is None:
        tools_dir = Path(__file__).parent

    # Import module
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        module_path,
        tools_dir / f"{module_path.replace('.', '/')}.py"
    )

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module '{module_path}'")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Get function
    func = getattr(module, function_name)
    return func


def print_tool_summary(tools_dir: Optional[Path] = None) -> None:
    """
    Print a human-readable summary of available tools.

    Useful for debugging and documentation.
    """
    tools = list_available_tools(tools_dir)

    if not tools:
        print("No tools found.")
        return

    print(f"Found {len(tools)} tool(s):\n")

    for tool_key, tool_info in sorted(tools.items()):
        print(f"📦 {tool_key}")
        print(f"   Function: {tool_info['function_name']}()")
        print(f"   Module: {tool_info['module_path']}")
        print(f"   Description: {tool_info['description'][:80]}...")
        print(f"   Parameters: {', '.join(tool_info['parameters'].keys())}")
        print()


if __name__ == "__main__":
    # When run directly, print tool summary
    print_tool_summary()
