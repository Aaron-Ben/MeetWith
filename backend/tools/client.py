"""
MCP Client Wrapper for MeetWith Plugin System

This module provides the call_mcp_tool() helper function that generated
tool functions use to execute plugins via the PluginManager.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MCPToolError(Exception):
    """Exception raised when MCP tool execution fails."""

    def __init__(self, tool_name: str, message: str, details: Optional[dict] = None):
        self.tool_name = tool_name
        self.message = message
        self.details = details or {}
        super().__init__(f"[{tool_name}] {message}")


class MCPTimeoutError(MCPToolError):
    """Exception raised when tool execution times out."""

    def __init__(self, tool_name: str, timeout_seconds: float):
        super().__init__(
            tool_name,
            f"Execution timed out after {timeout_seconds:.1f} seconds"
        )
        self.timeout_seconds = timeout_seconds


class MCPValidationError(MCPToolError):
    """Exception raised when tool input validation fails."""

    def __init__(self, tool_name: str, field: str, message: str):
        super().__init__(
            tool_name,
            f"Validation failed for field '{field}': {message}"
        )
        self.field = field


def _validate_input(
    tool_name: str,
    input_data: dict,
    schema: Optional[dict] = None
) -> None:
    """
    Validate input data against schema.

    Args:
        tool_name: Name of tool for error reporting
        input_data: Input dictionary to validate
        schema: Optional JSON schema for validation

    Raises:
        MCPValidationError: If validation fails
    """
    if not isinstance(input_data, dict):
        raise MCPValidationError(tool_name, 'input', 'Must be a dictionary')

    # Basic validation if no schema provided
    if not schema:
        return

    # Check required fields
    required = schema.get('required', [])
    properties = schema.get('properties', {})

    for field in required:
        if field not in input_data:
            raise MCPValidationError(
                tool_name,
                field,
                f"Required field '{field}' is missing"
            )

    # Type checking
    for field, value in input_data.items():
        if field not in properties:
            continue

        field_schema = properties[field]
        expected_type = field_schema.get('type')

        if value is None:
            continue  # None is allowed for optional fields

        type_map = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict
        }

        expected_python_type = type_map.get(expected_type)
        if expected_python_type and not isinstance(value, expected_python_type):
            raise MCPValidationError(
                tool_name,
                field,
                f"Expected type {expected_type}, got {type(value).__name__}"
            )

        # Range validation for numbers
        if expected_type in ['integer', 'number'] and isinstance(value, (int, float)):
            minimum = field_schema.get('minimum')
            maximum = field_schema.get('maximum')

            if minimum is not None and value < minimum:
                raise MCPValidationError(
                    tool_name,
                    field,
                    f"Value {value} is below minimum {minimum}"
                )

            if maximum is not None and value > maximum:
                raise MCPValidationError(
                    tool_name,
                    field,
                    f"Value {value} is above maximum {maximum}"
                )


def _get_plugin_manager():
    """
    Lazy import and get plugin manager singleton.

    This avoids circular imports and allows the client to be used
    independently of the server.
    """
    from plugin_manager import plugin_manager
    return plugin_manager


def with_timeout(timeout_seconds: float):
    """
    Decorator to add timeout to async function.

    Args:
        timeout_seconds: Maximum execution time in seconds
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                # Try to extract tool_name from args
                tool_name = kwargs.get('tool_name', args[0] if args else 'unknown')
                raise MCPTimeoutError(tool_name, timeout_seconds)
        return wrapper
    return decorator


@with_timeout(timeout_seconds=30.0)
async def call_mcp_tool(
    tool_name: str,
    input_data: Dict[str, Any],
    schema: Optional[dict] = None
) -> Any:
    """
    Execute an MCP tool by calling the underlying plugin.

    This is the core function that all generated tool wrappers use.
    It handles validation, execution, and error handling.

    Args:
        tool_name: Name of the tool/plugin to execute
        input_data: Dictionary of input parameters
        schema: Optional JSON schema for input validation

    Returns:
        The result from the tool execution (typically a dict)

    Raises:
        MCPValidationError: If input validation fails
        MCPTimeoutError: If execution times out
        MCPToolError: For other execution errors

    Example:
        >>> result = await call_mcp_tool(
        ...     tool_name='TavilySearch',
        ...     input_data={'query': 'Python tutorial', 'max_results': 5}
        ... )
        >>> print(result['results'][0]['title'])
    """
    start_time = datetime.now()

    # Validate input
    try:
        _validate_input(tool_name, input_data, schema)
    except MCPValidationError:
        raise
    except Exception as e:
        raise MCPToolError(
            tool_name,
            f"Unexpected validation error: {str(e)}"
        )

    # Get plugin manager
    try:
        plugin_manager = _get_plugin_manager()
    except Exception as e:
        raise MCPToolError(
            tool_name,
            f"Failed to access plugin manager: {str(e)}"
        )

    # Execute tool
    try:
        logger.info(f"[MCP] Executing tool: {tool_name} with input: {str(input_data)[:100]}")

        result = await plugin_manager.process_tool_call(
            tool_name=tool_name,
            tool_args=input_data
        )

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"[MCP] Tool {tool_name} completed in {elapsed:.2f}s")

        return result

    except ValueError as e:
        # Plugin manager validation errors
        raise MCPToolError(tool_name, str(e))
    except TimeoutError as e:
        # Convert to MCP timeout
        elapsed = (datetime.now() - start_time).total_seconds()
        raise MCPTimeoutError(tool_name, elapsed)
    except MCPToolError:
        # Re-raise MCP errors as-is
        raise
    except Exception as e:
        # Wrap other exceptions
        raise MCPToolError(
            tool_name,
            f"Execution failed: {str(e)}",
            details={'type': type(e).__name__}
        )


# Convenience function for typed calls
async def call_mcp_tool_typed(
    tool_name: str,
    input_data: Dict[str, Any],
    return_type: type,
    schema: Optional[dict] = None
) -> Any:
    """
    Typed version of call_mcp_tool for better IDE support.

    Args:
        tool_name: Name of the tool/plugin to execute
        input_data: Dictionary of input parameters
        return_type: Expected return type (for type checking)
        schema: Optional JSON schema for input validation

    Returns:
        The result from the tool execution, cast to return_type
    """
    result = await call_mcp_tool(tool_name, input_data, schema)
    return return_type(result)
