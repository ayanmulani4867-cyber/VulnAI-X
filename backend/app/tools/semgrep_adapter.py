import os
import re
import json
import shutil
import time
from typing import Dict, Any, List
from app.tools.base import BaseToolAdapter, ToolExecutionResult

# Built-in lightweight SAST patterns for when Semgrep CLI is not installed
BUILTIN_PATTERNS = [
    {
        "id": "vulnai.generic.hardcoded-aws-key",
        "name": "Hardcoded AWS Access Key",
        "pattern": r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
        "severity": "Critical",
        "category": "Hardcoded Secret",
        "remediation": "Revoke the key immediately and load credentials via environment variables or IAM roles."
    },
    {
        "id": "vulnai.generic.hardcoded-github-token",
        "name": "Hardcoded GitHub Personal Access Token",
        "pattern": r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,255}",
        "severity": "Critical",
        "category": "Hardcoded Secret",
        "remediation": "Revoke the GitHub token and use repository secrets or environment variables."
    },
    {
        "id": "vulnai.generic.insecure-eval",
        "name": "Dangerous Execution of Dynamic Code (eval/exec)",
        "pattern": r"\b(eval|exec)\s*\([^)]+\)",
        "severity": "High",
        "category": "Code Injection",
        "remediation": "Avoid using eval() or exec() with dynamic or user-controlled input. Use safe parsers like ast.literal_eval."
    },
    {
        "id": "vulnai.generic.sql-injection-format",
        "name": "Potential SQL Injection via String Interpolation",
        "pattern": r"\.(?:execute|raw)\s*\(\s*f[\"'].*?(?:SELECT|INSERT|UPDATE|DELETE).*?\{",
        "severity": "High",
        "category": "SQL Injection",
        "remediation": "Use parameterized queries or ORM query builders instead of f-strings or string concatenation."
    },
    {
        "id": "vulnai.generic.subprocess-shell-true",
        "name": "Subprocess Executed with shell=True",
        "pattern": r"subprocess\.(?:Popen|run|call|check_output)\s*\([^)]*shell\s*=\s*True",
        "severity": "High",
        "category": "Command Injection",
        "remediation": "Pass command arguments as a list of strings and set shell=False."
    },
    {
        "id": "vulnai.generic.insecure-deserialization-pickle",
        "name": "Insecure Deserialization via pickle",
        "pattern": r"pickle\.(?:loads|load)\s*\(",
        "severity": "Critical",
        "category": "Insecure Deserialization",
        "remediation": "Do not deserialize untrusted data with pickle. Use safe serialization formats such as JSON or Protocol Buffers."
    },
    {
        "id": "vulnai.generic.weak-crypto-hash",
        "name": "Use of Cryptographically Weak Hash (MD5 / SHA1)",
        "pattern": r"hashlib\.(?:md5|sha1)\s*\(",
        "severity": "Medium",
        "category": "Cryptography",
        "remediation": "Use SHA-256, SHA-3, or password-hashing algorithms like Argon2 or bcrypt for passwords."
    }
]

class SemgrepAdapter(BaseToolAdapter):
    tool_name = "semgrep"

    def is_available(self) -> bool:
        return shutil.which("semgrep") is not None

    def scan_path(self, target_path: str, timeout: int = 180) -> ToolExecutionResult:
        start_time = time.time()
        
        # 1. If Semgrep CLI is available, run it
        if self.is_available():
            cmd = ["semgrep", "scan", "--json", "--quiet", "--config", "auto", target_path]
            res = self.run_safe_subprocess(cmd, timeout=timeout)
            if res.success and res.raw_output:
                try:
                    data = json.loads(res.raw_output)
                    res.structured_data = data
                    return res
                except json.JSONDecodeError:
                    pass

        # 2. Resilient Fallback: Built-in SAST rule runner
        findings = []
        if os.path.exists(target_path):
            files_to_scan = []
            if os.path.isfile(target_path):
                files_to_scan.append(target_path)
            else:
                for root, _, files in os.walk(target_path):
                    for file in files:
                        if file.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".php", ".env", ".json", ".yaml", ".yml")):
                            files_to_scan.append(os.path.join(root, file))

            for filepath in files_to_scan[:500]: # bounded scan limit
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        for line_idx, line in enumerate(lines):
                            for rule in BUILTIN_PATTERNS:
                                if re.search(rule["pattern"], line):
                                    findings.append({
                                        "check_id": rule["id"],
                                        "path": os.path.relpath(filepath, target_path) if target_path != filepath else filepath,
                                        "start": {"line": line_idx + 1},
                                        "extra": {
                                            "message": rule["name"],
                                            "severity": rule["severity"].upper(),
                                            "category": rule["category"],
                                            "remediation": rule["remediation"],
                                            "lines": line.strip()
                                        }
                                    })
                except Exception:
                    continue

        elapsed = int((time.time() - start_time) * 1000)
        return ToolExecutionResult(
            tool_name=self.tool_name,
            success=True,
            raw_output=f"Scanned using VulnAI Semgrep Engine. Found {len(findings)} potential security findings.",
            structured_data={"results": findings},
            execution_time_ms=elapsed,
            exit_code=0
        )
