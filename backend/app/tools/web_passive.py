import urllib.parse
import ssl
import socket
import time
from typing import Dict, Any, List
from app.tools.base import BaseToolAdapter, ToolExecutionResult
from app.security.ssrf_protection import validate_network_target, safe_http_request, SSRFSecurityError

class WebPassiveAnalyzer(BaseToolAdapter):
    tool_name = "web_passive_analyzer"

    async def scan_target(self, target_url: str) -> ToolExecutionResult:
        start_time = time.time()
        findings = []
        structured_data: Dict[str, Any] = {
            "target": target_url,
            "security_headers": {},
            "cookies": [],
            "tls_info": {},
            "exposed_files": []
        }

        # 1. SSRF Guard
        is_safe, msg, _ = validate_network_target(target_url)
        if not is_safe:
            return ToolExecutionResult(
                tool_name=self.tool_name,
                success=False,
                raw_output=f"Target rejected by SSRF guard: {msg}",
                error_message=msg
            )

        parsed = urllib.parse.urlparse(target_url if "://" in target_url else f"https://{target_url}")
        target_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # 2. Main page request
        try:
            resp = await safe_http_request(target_url, method="GET", timeout=12)
            headers = {k.lower(): v for k, v in resp.headers.items()}
            structured_data["status_code"] = resp.status_code
            structured_data["headers"] = dict(resp.headers)

            # Check Security Headers
            header_checks = [
                {
                    "name": "strict-transport-security",
                    "title": "Missing HTTP Strict Transport Security (HSTS)",
                    "severity": "Medium",
                    "category": "Security Headers",
                    "remediation": "Enable HSTS by sending 'Strict-Transport-Security: max-age=31536000; includeSubDomains; preload'."
                },
                {
                    "name": "content-security-policy",
                    "title": "Missing Content-Security-Policy (CSP)",
                    "severity": "Medium",
                    "category": "Security Headers",
                    "remediation": "Define a robust Content-Security-Policy to mitigate Cross-Site Scripting (XSS) and data injection attacks."
                },
                {
                    "name": "x-frame-options",
                    "title": "Missing Anti-Clickjacking Header (X-Frame-Options / frame-ancestors)",
                    "severity": "Low",
                    "category": "Security Headers",
                    "remediation": "Configure X-Frame-Options: DENY or SAMEORIGIN, or CSP frame-ancestors directive."
                },
                {
                    "name": "x-content-type-options",
                    "title": "Missing X-Content-Type-Options Header",
                    "severity": "Low",
                    "category": "Security Headers",
                    "remediation": "Set 'X-Content-Type-Options: nosniff' to prevent MIME-type confusion attacks."
                },
                {
                    "name": "referrer-policy",
                    "title": "Missing Referrer-Policy Header",
                    "severity": "Informational",
                    "category": "Security Headers",
                    "remediation": "Set 'Referrer-Policy: strict-origin-when-cross-origin' to prevent URL parameter leakage in Referer header."
                }
            ]

            for check in header_checks:
                val = headers.get(check["name"])
                structured_data["security_headers"][check["name"]] = val or "MISSING"
                if not val:
                    # If CSP missing, check if frame-ancestors in CSP or x-frame-options
                    findings.append({
                        "title": check["title"],
                        "category": check["category"],
                        "severity": check["severity"],
                        "confidence": "Certain",
                        "evidence": f"Header '{check['name']}' was not present in HTTP response headers.",
                        "impact": f"Target application lacks recommended browser security defense ({check['name']}).",
                        "remediation": check["remediation"],
                        "rule_id": f"vulnai.headers.{check['name']}"
                    })

            # Check Cookie Security Attributes
            set_cookie_headers = resp.headers.get_list("set-cookie") if hasattr(resp.headers, "get_list") else [resp.headers.get("set-cookie", "")]
            for raw_cookie in set_cookie_headers:
                if not raw_cookie:
                    continue
                cookie_lower = raw_cookie.lower()
                cookie_name = raw_cookie.split("=")[0].strip()
                structured_data["cookies"].append(cookie_name)

                if "httponly" not in cookie_lower:
                    findings.append({
                        "title": f"Cookie '{cookie_name}' Missing HttpOnly Flag",
                        "category": "Cookie Security",
                        "severity": "Medium",
                        "confidence": "Certain",
                        "evidence": f"Set-Cookie header: {raw_cookie}",
                        "impact": "Cookie can be accessed by client-side JavaScript, increasing risk in event of XSS.",
                        "remediation": "Add the 'HttpOnly' attribute to all sensitive session and authentication cookies.",
                        "rule_id": "vulnai.cookie.missing-httponly"
                    })

                if "secure" not in cookie_lower and parsed.scheme == "https":
                    findings.append({
                        "title": f"Cookie '{cookie_name}' Missing Secure Flag",
                        "category": "Cookie Security",
                        "severity": "Medium",
                        "confidence": "Certain",
                        "evidence": f"Set-Cookie header: {raw_cookie}",
                        "impact": "Cookie may be transmitted over unencrypted HTTP connections.",
                        "remediation": "Add the 'Secure' attribute to ensure transmission only over TLS.",
                        "rule_id": "vulnai.cookie.missing-secure"
                    })

                if "samesite" not in cookie_lower:
                    findings.append({
                        "title": f"Cookie '{cookie_name}' Missing SameSite Attribute",
                        "category": "Cookie Security",
                        "severity": "Low",
                        "confidence": "Certain",
                        "evidence": f"Set-Cookie header: {raw_cookie}",
                        "impact": "Browser default handling may allow CSRF in certain contexts.",
                        "remediation": "Set 'SameSite=Lax' or 'SameSite=Strict' on session cookies.",
                        "rule_id": "vulnai.cookie.missing-samesite"
                    })

        except Exception as e:
            return ToolExecutionResult(
                tool_name=self.tool_name,
                success=False,
                raw_output=f"HTTP request error: {str(e)}",
                error_message=str(e)
            )

        # 3. Check TLS Configuration
        if parsed.scheme == "https" and parsed.hostname:
            try:
                context = ssl.create_default_context()
                with socket.create_connection((parsed.hostname, parsed.port or 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=parsed.hostname) as ssock:
                        tls_version = ssock.version()
                        cipher = ssock.cipher()
                        structured_data["tls_info"] = {
                            "version": tls_version,
                            "cipher": cipher[0] if cipher else "Unknown",
                            "bits": cipher[2] if cipher else 0
                        }
                        if tls_version in ("TLSv1", "TLSv1.1", "SSLv3"):
                            findings.append({
                                "title": f"Deprecated TLS Protocol Version Supported: {tls_version}",
                                "category": "TLS Configuration",
                                "severity": "High",
                                "confidence": "Certain",
                                "evidence": f"Negotiated TLS version: {tls_version} using cipher {cipher}",
                                "impact": "Vulnerable to cryptographic downgrade and deprecated cipher suite attacks.",
                                "remediation": "Disable TLS 1.0 and 1.1. Enforce TLS 1.2 or TLS 1.3.",
                                "rule_id": "vulnai.tls.deprecated-version"
                            })
            except Exception:
                pass

        # 4. Check for Exposed Sensitive Files (robots.txt, security.txt, .git probe)
        sensitive_paths = [
            ("robots.txt", "Robots.txt Information Disclosure"),
            (".well-known/security.txt", "Security.txt Responsible Disclosure Policy"),
            (".git/HEAD", "Exposed .git Source Code Repository"),
            (".env", "Exposed Environment Configuration File")
        ]

        base_url = f"{parsed.scheme}://{parsed.netloc}"
        for path, desc in sensitive_paths:
            probe_url = f"{base_url}/{path}"
            try:
                p_resp = await safe_http_request(probe_url, method="GET", timeout=5)
                if p_resp.status_code == 200:
                    text_sample = p_resp.text[:300]
                    if path == ".git/HEAD" and "ref: refs/" in text_sample:
                        findings.append({
                            "title": "Critical Exposure: Git Repository Exposed (.git/HEAD)",
                            "category": "Information Disclosure",
                            "severity": "Critical",
                            "confidence": "Certain",
                            "evidence": f"URL: {probe_url}\nContent snippet:\n{text_sample}",
                            "impact": "Attackers can download full source code, configuration history, and secrets.",
                            "remediation": "Restrict web server access to the .git directory immediately.",
                            "rule_id": "vulnai.exposure.git-head"
                        })
                    elif path == ".env" and ("DB_" in text_sample or "SECRET" in text_sample or "API_KEY" in text_sample):
                        findings.append({
                            "title": "Critical Exposure: Environment File Exposed (.env)",
                            "category": "Information Disclosure",
                            "severity": "Critical",
                            "confidence": "Certain",
                            "evidence": f"URL: {probe_url}\nSensitive keys detected in response.",
                            "impact": "Complete compromise of backend secrets, database passwords, and API credentials.",
                            "remediation": "Block public access to .env files in web server (Nginx/Apache) configuration.",
                            "rule_id": "vulnai.exposure.dotenv"
                        })
                    structured_data["exposed_files"].append({"path": path, "status": p_resp.status_code})
            except Exception:
                continue

        elapsed = int((time.time() - start_time) * 1000)
        return ToolExecutionResult(
            tool_name=self.tool_name,
            success=True,
            raw_output=f"Passive web analysis completed. Discovered {len(findings)} findings.",
            structured_data={"findings": findings, **structured_data},
            execution_time_ms=elapsed,
            exit_code=0
        )
