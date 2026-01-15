"""
Python Code Execution Environment for MCP Hybrid Approach

This module provides a safe Python code executor that allows AI to write
and execute Python code for complex data processing and tool coordination.
"""

import asyncio
import io
import sys
import os
import logging
import traceback
from typing import Any, Dict, Optional
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime

logger = logging.getLogger(__name__)


class CodeExecutionError(Exception):
    """Exception raised when code execution fails."""
    pass


class CodeTimeoutError(CodeExecutionError):
    """Exception raised when code execution times out."""
    pass


class OutputCapture:
    """
    Context manager to capture stdout/stderr during code execution.

    Example:
        with OutputCapture() as capture:
            print("Hello")
        print(capture.get_output())  # "Hello"
    """

    def __init__(self):
        self.stdout_buffer = io.StringIO()
        self.stderr_buffer = io.StringIO()
        self.original_stdout = None
        self.original_stderr = None

    def get_output(self) -> str:
        """Get captured stdout."""
        return self.stdout_buffer.getvalue()

    def get_error(self) -> str:
        """Get captured stderr."""
        return self.stderr_buffer.getvalue()

    def get_all(self) -> str:
        """Get all captured output (stdout + stderr)."""
        output = self.get_output()
        error = self.get_error()
        if output and error:
            return output + "\n" + error
        return output or error

    def __enter__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self.stdout_buffer
        sys.stderr = self.stderr_buffer
        return self

    def __exit__(self, *args):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr


class CodeExecutor:
    """
    Safe Python code executor for AI-generated code.

    Features:
    - Async function execution support
    - Stdout/stderr capture
    - Timeout protection
    - Error handling
    - Available imports: tools.*, asyncio, json, re, etc.
    """

    def __init__(self, timeout: float = 30.0):
        """
        Initialize the code executor.

        Args:
            timeout: Maximum execution time in seconds (default: 30)
        """
        self.timeout = timeout
        self.execution_globals = self._create_safe_globals()

    def _create_safe_globals(self) -> Dict[str, Any]:
        """
        Create a safe global namespace for code execution.

        Includes:
        - Standard library modules (asyncio, json, re, os, etc.)
        - Generated tools (tools.*)
        - Utility functions (print, len, etc.)
        """
        # Import tools module
        import importlib
        import tools
        import tools.client
        import tools.search_tools

        globals_dict = {
            # Standard library modules
            '__builtins__': {
                'print': print,
                'len': len,
                'range': range,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'min': min,
                'max': max,
                'sum': sum,
                'abs': abs,
                'round': round,
                'enumerate': enumerate,
                'zip': zip,
                'sorted': sorted,
                'map': map,
                'filter': filter,
                'any': any,
                'all': all,
                'isinstance': isinstance,
                'type': type,
                'help': help,
                'dir': dir,
            },
            # Async support
            'asyncio': asyncio,
            # Data processing
            'json': __import__('json'),
            're': __import__('re'),
            # File operations
            'os': os,
            'pathlib': __import__('pathlib'),
            # Date/time
            'datetime': datetime,
            # Tools
            'tools': tools,
            'call_mcp_tool': tools.client.call_mcp_tool,
            'list_available_tools': tools.search_tools.list_available_tools,
            'search_tools': tools.search_tools.search_tools,
        }

        # Add all tool modules dynamically
        try:
            tools_dir = os.path.dirname(tools.__file__)
            for item in os.listdir(tools_dir):
                item_path = os.path.join(tools_dir, item)
                if os.path.isdir(item_path) and not item.startswith('_'):
                    try:
                        module = importlib.import_module(f'tools.{item}')
                        globals_dict[item] = module
                    except ImportError:
                        logger.warning(f"Could not import tools.{item}")
        except Exception as e:
            logger.warning(f"Error loading tool modules: {e}")

        return globals_dict

    async def execute_code(self, code: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Execute Python code and return output.

        Args:
            code: Python code to execute
            timeout: Maximum execution time in seconds (overrides default)

        Returns:
            {
                'success': bool,
                'output': str,  # stdout
                'error': str,   # stderr or exception message
                'result': Any,  # return value of last expression (if any)
                'execution_time': float  # time taken in seconds
            }

        Raises:
            CodeTimeoutError: If execution times out
            CodeExecutionError: For other execution errors
        """
        if timeout is None:
            timeout = self.timeout

        start_time = datetime.now()
        result = None

        try:
            # Execute code with output capture
            with OutputCapture() as capture:
                # Prepare execution environment
                exec_locals = {}
                exec_globals = self.execution_globals.copy()

                # Execute the code
                try:
                    # First, try to execute as a block of code
                    exec(code, exec_globals, exec_locals)

                    # Check if there's a last expression that could be a result
                    # (for single-line expressions like "2 + 2")
                    if code.strip() and not code.strip().startswith('#'):
                        lines = [line.strip() for line in code.strip().split('\n') if line.strip()]
                        last_line = lines[-1] if lines else ''

                        # Try to eval the last line if it looks like an expression
                        if (last_line and
                            not last_line.startswith(('def', 'class', 'if', 'for', 'while', 'try', 'with', 'import', 'from', 'async', 'await'))):
                            try:
                                result = eval(last_line, exec_globals, exec_locals)
                            except:
                                result = None

                except Exception as e:
                    # If exec fails, try eval for single expressions
                    try:
                        result = eval(code, exec_globals, exec_locals)
                    except Exception as eval_error:
                        raise CodeExecutionError(f"Execution failed: {str(eval_error)}")

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            # Get captured output
            output = capture.get_output()
            error = capture.get_error()

            # Build result
            return {
                'success': True,
                'output': output,
                'error': error,
                'result': result,
                'execution_time': execution_time
            }

        except asyncio.TimeoutError:
            execution_time = (datetime.now() - start_time).total_seconds()
            raise CodeTimeoutError(f"Code execution timed out after {execution_time:.2f} seconds")

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Code execution error: {error_msg}")

            return {
                'success': False,
                'output': '',
                'error': error_msg,
                'result': None,
                'execution_time': execution_time
            }

    async def execute_code_with_timeout(self, code: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Execute code with timeout protection.

        This is a wrapper around execute_code that ensures timeout is enforced.
        """
        if timeout is None:
            timeout = self.timeout

        try:
            return await asyncio.wait_for(
                self.execute_code(code, timeout),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            execution_time = timeout
            raise CodeTimeoutError(f"Code execution timed out after {execution_time:.2f} seconds")


# Singleton instance
_code_executor_instance = None


def get_code_executor(timeout: float = 30.0) -> CodeExecutor:
    """
    Get the singleton CodeExecutor instance.

    Args:
        timeout: Timeout in seconds (only used on first call)

    Returns:
        CodeExecutor instance
    """
    global _code_executor_instance
    if _code_executor_instance is None:
        _code_executor_instance = CodeExecutor(timeout=timeout)
    return _code_executor_instance


async def execute_ai_code(code: str, timeout: float = 30.0) -> Dict[str, Any]:
    """
    Convenience function to execute AI-generated code.

    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds

    Returns:
        Execution result dict

    Example:
        >>> result = await execute_ai_code("print('Hello, World!')")
        >>> print(result['output'])
        Hello, World!
    """
    executor = get_code_executor(timeout=timeout)
    return await executor.execute_code_with_timeout(code, timeout)
