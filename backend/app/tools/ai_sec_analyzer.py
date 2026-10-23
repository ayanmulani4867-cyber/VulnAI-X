import os
import re
import time
from typing import Dict, Any, List
from app.tools.base import BaseToolAdapter, ToolExecutionResult

AI_SECURITY_RULES = [
    {
        "id": "vulnai.aisec.direct-prompt-concatenation",
        "title": "Unsanitized User Input Concatenated Directly into LLM Prompt",
        "pattern": r'(?:messages|prompt)\s*=\s*f?["\'].*?\{user_input|\.format\(.*?user_input',
        "severity": "High",
        "category": "AI Security",
        "impact": "Enables direct or indirect Prompt Injection attacks that can alter model behavior or leak system instructions.",
        "remediation": "Use structured message roles (system, user, assistant) and enforce input sanitization and boundary demarcations."
    },
    {
        "id": "vulnai.aisec.unsafe-llm-code-execution",
        "title": "Unsafe Execution of LLM Output (eval/exec)",
        "pattern": r'(?:eval|exec)\s*\(\s*(?:response|output|completion|llm_output)',
        "severity": "Critical",
        "category": "AI Security",
        "impact": "Allows arbitrary Remote Code Execution (RCE) if the LLM output is influenced by untrusted input or prompt injection.",
        "remediation": "Never pass LLM text outputs directly to eval() or exec(). Use safe, isolated sandboxes and strict AST verification."
    },
    {
        "id": "vulnai.aisec.unrestricted-tool-execution",
        "title": "LLM Function / Tool Call Executes System Commands without Sandboxing",
        "pattern": r'def\s+(?:run_bash|execute_command|run_shell)\s*\([^)]*\):.*?subprocess',
        "severity": "Critical",
        "category": "AI Security",
        "impact": "Autonomous tool calling allows prompt injections to trigger arbitrary commands on host.",
        "remediation": "Restrict agent tool actions, implement human-in-the-loop approvals, and run tool execution in ephemeral containers."
    },
    {
        "id": "vulnai.aisec.exposed-openai-key",
        "title": "Hardcoded AI Provider API Key Detected",
        "pattern": r'(?:sk-[a-zA-Z0-9_-]{32,}|AIza[0-9A-Za-z\-_]{35}|ant-api03-[a-zA-Z0-9_\-]{32,})',
        "severity": "Critical",
        "category": "Hardcoded Secret",
        "impact": "Unauthorized actors can consume model credits, access internal assistant threads, or fine-tune models.",
        "remediation": "Store AI provider API keys in environment variables or key vaults."
    }
]

class AISecAnalyzer(BaseToolAdapter):
    tool_name = "ai_sec_analyzer"

    def scan_path(self, target_path: str) -> ToolExecutionResult:
        start_time = time.time()
        findings = []

        if not os.path.exists(target_path):
            return ToolExecutionResult(
                tool_name=self.tool_name,
                success=False,
                raw_output="",
                error_message=f"Target path '{target_path}' does not exist."
            )

        files_to_scan = []
        if os.path.isfile(target_path):
            files_to_scan.append(target_path)
        else:
            for root, _, files in os.walk(target_path):
                for f in files:
                    if f.endswith((".py", ".js", ".ts", ".json", ".yaml", ".env")):
                        files_to_scan.append(os.path.join(root, f))

        for fpath in files_to_scan[:300]:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                for rule in AI_SECURITY_RULES:
                    match = re.search(rule["pattern"], content, re.DOTALL | re.IGNORECASE)
                    if match:
                        findings.append({
                            "title": rule["title"],
                            "category": rule["category"],
                            "severity": rule["severity"],
                            "confidence": "High",
                            "evidence": f"File: {os.path.basename(fpath)}\nSnippet: {match.group(0)[:150]}",
                            "impact": rule["impact"],
                            "remediation": rule["remediation"],
                            "rule_id": rule["id"]
                        })
            except Exception:
                continue

        elapsed = int((time.time() - start_time) * 1000)
        return ToolExecutionResult(
            tool_name=self.tool_name,
            success=True,
            raw_output=f"AI security audit completed. Found {len(findings)} potential AI vulnerabilities.",
            structured_data={"findings": findings},
            execution_time_ms=elapsed,
            exit_code=0
        )
