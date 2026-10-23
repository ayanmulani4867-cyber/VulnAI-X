import subprocess
import shutil
import time
from typing import Dict, Any, List, Optional
import json

class ToolExecutionResult:
    def __init__(
        self,
        tool_name: str,
        success: bool,
        raw_output: str,
        structured_data: Optional[Dict[str, Any]] = None,
        execution_time_ms: int = 0,
        exit_code: int = 0,
        error_message: Optional[str] = None
    ):
        self.tool_name = tool_name
        self.success = success
        self.raw_output = raw_output
        self.structured_data = structured_data or {}
        self.execution_time_ms = execution_time_ms
        self.exit_code = exit_code
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "raw_output": self.raw_output,
            "structured_data": self.structured_data,
            "execution_time_ms": self.execution_time_ms,
            "exit_code": self.exit_code,
            "error_message": self.error_message
        }

class BaseToolAdapter:
    tool_name: str = "base_tool"

    def is_available(self) -> bool:
        """Checks if the CLI tool or runtime is installed on the host."""
        return True

    def run_safe_subprocess(
        self,
        cmd_args: List[str],
        cwd: Optional[str] = None,
        timeout: int = 120
    ) -> ToolExecutionResult:
        """
        Executes an external command safely using an argument array.
        Never uses shell=True to prevent shell injection vulnerabilities.
        """
        start_time = time.time()
        try:
            # Check executable exists
            exe = shutil.which(cmd_args[0])
            if not exe:
                return ToolExecutionResult(
                    tool_name=self.tool_name,
                    success=False,
                    raw_output="",
                    exit_code=127,
                    error_message=f"Executable '{cmd_args[0]}' is not found in system PATH."
                )

            # Replace first element with resolved executable path
            resolved_args = [exe] + cmd_args[1:]

            process = subprocess.run(
                resolved_args,
                cwd=cwd,
                capture_output=True,
                text=True,
                shell=False, # Mandatory security control: no shell interpolation
                timeout=timeout
            )
            
            elapsed = int((time.time() - start_time) * 1000)
            return ToolExecutionResult(
                tool_name=self.tool_name,
                success=(process.returncode == 0),
                raw_output=process.stdout + ("\n" + process.stderr if process.stderr else ""),
                execution_time_ms=elapsed,
                exit_code=process.returncode
            )
        except subprocess.TimeoutExpired:
            elapsed = int((time.time() - start_time) * 1000)
            return ToolExecutionResult(
                tool_name=self.tool_name,
                success=False,
                raw_output="Subprocess timed out.",
                execution_time_ms=elapsed,
                exit_code=-1,
                error_message=f"Execution timed out after {timeout} seconds."
            )
        except Exception as e:
            elapsed = int((time.time() - start_time) * 1000)
            return ToolExecutionResult(
                tool_name=self.tool_name,
                success=False,
                raw_output=str(e),
                execution_time_ms=elapsed,
                exit_code=-1,
                error_message=f"Subprocess execution error: {str(e)}"
            )
