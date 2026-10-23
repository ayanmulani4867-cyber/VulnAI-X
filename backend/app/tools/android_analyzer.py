import os
import re
import xml.etree.ElementTree as ET
import zipfile
import time
from typing import Dict, Any, List
from app.tools.base import BaseToolAdapter, ToolExecutionResult

DANGEROUS_PERMISSIONS = {
    "android.permission.READ_CONTACTS",
    "android.permission.WRITE_CONTACTS",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.RECORD_AUDIO",
    "android.permission.CAMERA",
    "android.permission.READ_SMS",
    "android.permission.SEND_SMS",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE"
}

class AndroidStaticAnalyzer(BaseToolAdapter):
    tool_name = "android_static_analyzer"

    def analyze_target(self, target_path: str) -> ToolExecutionResult:
        start_time = time.time()
        findings = []
        metadata = {
            "permissions": [],
            "dangerous_permissions": [],
            "exported_components": [],
            "debuggable": False,
            "cleartext_traffic": False,
            "hardcoded_secrets": []
        }

        if not os.path.exists(target_path):
            return ToolExecutionResult(
                tool_name=self.tool_name,
                success=False,
                raw_output="",
                error_message=f"Target Android path or APK '{target_path}' does not exist."
            )

        manifest_content = ""
        # Check if target is an APK file or a project directory
        if target_path.lower().endswith(".apk") and zipfile.is_zipfile(target_path):
            # Extract strings and examine APK archive safely without executing
            try:
                with zipfile.ZipFile(target_path, "r") as z:
                    for name in z.namelist():
                        if name.endswith("AndroidManifest.xml"):
                            # Binary XML or plain XML
                            raw = z.read(name)
                            # Extract ASCII strings from binary XML or plain
                            manifest_content = "".join([chr(b) if 32 <= b <= 126 or b in (10, 13) else " " for b in raw])
                            break
            except Exception as e:
                return ToolExecutionResult(
                    tool_name=self.tool_name,
                    success=False,
                    raw_output=f"Error inspecting APK zip archive: {str(e)}"
                )
        else:
            # Check for AndroidManifest.xml in directory
            for root, _, files in os.walk(target_path):
                if "AndroidManifest.xml" in files:
                    m_path = os.path.join(root, "AndroidManifest.xml")
                    try:
                        with open(m_path, "r", encoding="utf-8", errors="ignore") as f:
                            manifest_content = f.read()
                            break
                    except Exception:
                        pass

        if not manifest_content:
            return ToolExecutionResult(
                tool_name=self.tool_name,
                success=False,
                raw_output="No AndroidManifest.xml or valid APK structure found at target path."
            )

        # 1. Check Debuggable Flag
        if 'android:debuggable="true"' in manifest_content or 'debuggable="true"' in manifest_content:
            metadata["debuggable"] = True
            findings.append({
                "title": "Android Application Marked as Debuggable",
                "category": "Mobile Security",
                "severity": "High",
                "confidence": "Certain",
                "evidence": "android:debuggable=\"true\" found in AndroidManifest.xml",
                "impact": "Enables debugging in production, allowing attackers or malware to attach debuggers and dump runtime memory/keys.",
                "remediation": "Set android:debuggable=\"false\" in production release builds.",
                "rule_id": "vulnai.android.debuggable-true"
            })

        # 2. Check Cleartext Traffic
        if 'android:usesCleartextTraffic="true"' in manifest_content or 'usesCleartextTraffic="true"' in manifest_content:
            metadata["cleartext_traffic"] = True
            findings.append({
                "title": "Cleartext HTTP Traffic Permitted (usesCleartextTraffic=true)",
                "category": "Mobile Security",
                "severity": "Medium",
                "confidence": "Certain",
                "evidence": "android:usesCleartextTraffic=\"true\" enabled.",
                "impact": "Allows network requests over unencrypted HTTP, leaving app vulnerable to eavesdropping and MITM attacks.",
                "remediation": "Enforce HTTPS by setting android:usesCleartextTraffic=\"false\" and configure a Network Security Config.",
                "rule_id": "vulnai.android.cleartext-traffic"
            })

        # 3. Check Exported Components
        exported_matches = re.findall(r'<(?P<type>activity|service|receiver|provider)[^>]*?android:exported=["\']true["\'][^>]*?>', manifest_content, re.IGNORECASE)
        for comp_type in exported_matches:
            metadata["exported_components"].append(comp_type)

        if len(metadata["exported_components"]) > 0:
            findings.append({
                "title": f"Potentially Insecure Exported Android Components Found ({len(metadata['exported_components'])} components)",
                "category": "Mobile Security",
                "severity": "Medium",
                "confidence": "High",
                "evidence": f"Exported components detected: {', '.join(metadata['exported_components'][:5])}",
                "impact": "Exported activities, services, or broadcast receivers can be triggered by any other third-party app installed on the device.",
                "remediation": "Explicitly set android:exported=\"false\" for internal components, or protect them with custom signature-level permissions.",
                "rule_id": "vulnai.android.exported-component"
            })

        # 4. Check Dangerous Permissions
        perm_matches = re.findall(r'uses-permission[^>]*?android:name=["\']([^"\']+)["\']', manifest_content)
        for perm in perm_matches:
            metadata["permissions"].append(perm)
            if perm in DANGEROUS_PERMISSIONS:
                metadata["dangerous_permissions"].append(perm)

        if len(metadata["dangerous_permissions"]) >= 3:
            findings.append({
                "title": f"Excessive High-Risk Android Permissions Requested ({len(metadata['dangerous_permissions'])} permissions)",
                "category": "Mobile Security",
                "severity": "Low",
                "confidence": "High",
                "evidence": f"Dangerous permissions: {', '.join(metadata['dangerous_permissions'])}",
                "impact": "Broad device permissions expand attack surface and violate the principle of least privilege.",
                "remediation": "Review required permissions and request only what is strictly necessary at runtime.",
                "rule_id": "vulnai.android.excessive-permissions"
            })

        # 5. Search for Hardcoded Secrets
        secret_patterns = [
            ("Firebase Database URL", r'https://[a-zA-Z0-9_\-]+\.firebaseio\.com'),
            ("Google API Key", r'AIza[0-9A-Za-z\-_]{35}'),
            ("Insecure AES ECB Mode", r'AES/ECB/PKCS5Padding')
        ]
        for sec_name, sec_regex in secret_patterns:
            matches = re.findall(sec_regex, manifest_content)
            if matches:
                findings.append({
                    "title": f"Hardcoded Indicator Detected: {sec_name}",
                    "category": "Mobile Security",
                    "severity": "Medium",
                    "confidence": "High",
                    "evidence": f"Found match for pattern: {matches[0]}",
                    "impact": "Exposed keys or weak cryptographic modes in mobile code.",
                    "remediation": f"Remove {sec_name} and use Android Keystore or dynamic backend configuration.",
                    "rule_id": f"vulnai.android.{sec_name.lower().replace(' ', '-')}"
                })

        elapsed = int((time.time() - start_time) * 1000)
        return ToolExecutionResult(
            tool_name=self.tool_name,
            success=True,
            raw_output=f"Android static analysis completed. Found {len(findings)} issues.",
            structured_data={"metadata": metadata, "findings": findings},
            execution_time_ms=elapsed,
            exit_code=0
        )
