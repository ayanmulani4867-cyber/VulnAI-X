import os
import httpx
import time
from typing import Dict, Any, List
from app.tools.base import BaseToolAdapter, ToolExecutionResult
from app.tools.web_passive import WebPassiveAnalyzer

class ZapAdapter(BaseToolAdapter):
    tool_name = "owasp_zap"

    def __init__(self, zap_url: str = os.getenv("ZAP_API_URL", "http://127.0.0.1:8080"), zap_api_key: str = os.getenv("ZAP_API_KEY", "")):
        self.zap_url = zap_url
        self.zap_api_key = zap_api_key

    def is_available(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.zap_url}/JSON/core/view/version/", headers={"X-ZAP-API-Key": self.zap_api_key})
                return res.status_code == 200
        except Exception:
            return False

    async def run_passive_scan(self, target_url: str) -> ToolExecutionResult:
        start_time = time.time()
        # If live OWASP ZAP is available, query its alerts
        if self.is_available():
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(
                        f"{self.zap_url}/JSON/alert/view/alertsByRisk/",
                        params={"url": target_url},
                        headers={"X-ZAP-API-Key": self.zap_api_key}
                    )
                    if resp.status_code == 200:
                        elapsed = int((time.time() - start_time) * 1000)
                        return ToolExecutionResult(
                            tool_name=self.tool_name,
                            success=True,
                            raw_output="OWASP ZAP scan alerts retrieved.",
                            structured_data=resp.json(),
                            execution_time_ms=elapsed,
                            exit_code=0
                        )
            except Exception:
                pass

        # Fallback to VulnAI passive web analyzer
        analyzer = WebPassiveAnalyzer()
        res = await analyzer.scan_target(target_url)
        res.tool_name = self.tool_name
        return res
