import os
import re
import time
from typing import Dict, Any, List
from app.tools.base import BaseToolAdapter, ToolExecutionResult

IAC_RULES = [
    {
        "id": "vulnai.iac.s3-public-access",
        "title": "S3 Bucket Configured with Public Read / Write Access",
        "pattern": r'(?:acl\s*=\s*["\'](?:public-read|public-read-write)["\']|"Principal"\s*:\s*"\*")',
        "file_exts": [".tf", ".json", ".yaml", ".yml"],
        "severity": "Critical",
        "category": "Cloud Security",
        "impact": "Data stored in the S3 bucket is exposed to the public internet.",
        "remediation": "Enable S3 Block Public Access and use private bucket ACLs with IAM policies."
    },
    {
        "id": "vulnai.iac.open-ingress-ssh",
        "title": "Security Group Allows Inbound SSH (Port 22) from 0.0.0.0/0",
        "pattern": r'(?:from_port\s*=\s*22|to_port\s*=\s*22).*?(?:0\.0\.0\.0/0|::/0)',
        "file_exts": [".tf", ".json", ".yaml", ".yml"],
        "severity": "High",
        "category": "Cloud Security",
        "impact": "Exposes SSH management port to unrestricted internet-wide brute force attacks.",
        "remediation": "Restrict SSH ingress to specific corporate bastion IP addresses or use AWS Systems Manager Session Manager."
    },
    {
        "id": "vulnai.iac.docker-root-user",
        "title": "Dockerfile Runs as Default Root User",
        "pattern": r'^(?!.*\bUSER\s+[a-zA-Z0-9_\-]+).*$',
        "file_exts": ["dockerfile"],
        "severity": "Medium",
        "category": "Container Security",
        "impact": "Containers running as root increase risk of container breakout and privilege escalation.",
        "remediation": "Add 'USER nonroot' or create a dedicated service account in the Dockerfile."
    },
    {
        "id": "vulnai.iac.k8s-privileged-container",
        "title": "Kubernetes Pod Configured with Privileged Mode",
        "pattern": r'privileged:\s*true',
        "file_exts": [".yaml", ".yml"],
        "severity": "Critical",
        "category": "Container Security",
        "impact": "Privileged containers have full host access and can easily compromise node infrastructure.",
        "remediation": "Set securityContext.privileged: false and drop all unneeded Linux capabilities."
    },
    {
        "id": "vulnai.iac.unencrypted-storage",
        "title": "Cloud Storage Volume Created Without Encryption",
        "pattern": r'encrypted\s*=\s*false',
        "file_exts": [".tf"],
        "severity": "Medium",
        "category": "Cloud Security",
        "impact": "Data at rest is stored in plaintext on physical media.",
        "remediation": "Set encrypted = true and specify KMS customer managed keys."
    }
]

class CloudIaCAnalyzer(BaseToolAdapter):
    tool_name = "cloud_iac_analyzer"

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
                    files_to_scan.append(os.path.join(root, f))

        for fpath in files_to_scan[:300]:
            fname = os.path.basename(fpath).lower()
            _, ext = os.path.splitext(fname)
            
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                for rule in IAC_RULES:
                    applies = False
                    if "dockerfile" in rule["file_exts"] and "dockerfile" in fname:
                        applies = True
                    elif ext in rule["file_exts"]:
                        applies = True

                    if applies:
                        if rule["id"] == "vulnai.iac.docker-root-user":
                            # Check if USER instruction is present in Dockerfile
                            if not re.search(r'\bUSER\s+[a-zA-Z0-9_\-]+', content, re.IGNORECASE):
                                findings.append({
                                    "title": rule["title"],
                                    "category": rule["category"],
                                    "severity": rule["severity"],
                                    "confidence": "High",
                                    "evidence": f"File: {os.path.basename(fpath)} lacks a USER instruction.",
                                    "impact": rule["impact"],
                                    "remediation": rule["remediation"],
                                    "rule_id": rule["id"]
                                })
                        else:
                            match = re.search(rule["pattern"], content, re.DOTALL | re.IGNORECASE)
                            if match:
                                findings.append({
                                    "title": rule["title"],
                                    "category": rule["category"],
                                    "severity": rule["severity"],
                                    "confidence": "Certain",
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
            raw_output=f"Cloud IaC audit completed. Found {len(findings)} misconfigurations.",
            structured_data={"findings": findings},
            execution_time_ms=elapsed,
            exit_code=0
        )
