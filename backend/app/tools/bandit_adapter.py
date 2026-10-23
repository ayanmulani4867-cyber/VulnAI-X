import json
import os
import sys
from typing import Dict, Any, List
from app.tools.base import BaseToolAdapter, ToolExecutionResult

class BanditAdapter(BaseToolAdapter):
    tool_name = "bandit"

    def is_available(self) -> bool:
        # Check if bandit is available as CLI or python module
        try:
            import bandit
            return True
        except ImportError:
            return False

    def scan_path(self, target_path: str, timeout: int = 120) -> ToolExecutionResult:
        """
        Runs Bandit Python AST security scanner against target_path.
        """
        if not os.path.exists(target_path):
            return ToolExecutionResult(
                tool_name=self.tool_name,
                success=False,
                raw_output="",
                error_message=f"Target path '{target_path}' does not exist."
            )

        # Use current python executable to run bandit module safely
        cmd = [sys.executable, "-m", "bandit", "-r", target_path, "-f", "json", "-q"]
        result = self.run_safe_subprocess(cmd, timeout=timeout)
        
        # Bandit returns 0 when no issues, 1 when issues found
        structured = {"results": [], "errors": []}
        if result.raw_output:
            try:
                data = json.loads(result.raw_output)
                structured["results"] = data.get("results", [])
                structured["metrics"] = data.get("metrics", {})
                result.success = True
            except json.JSONDecodeError:
                structured["raw_snippet"] = result.raw_output[:500]

        result.structured_data = structured
        return result
