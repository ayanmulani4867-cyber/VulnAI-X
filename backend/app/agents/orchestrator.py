import asyncio
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import ResearchJob, Finding, Evidence, ToolResult, ScopeEntry
from app.security.scope_guard import validate_target_scope
from app.tools.web_passive import WebPassiveAnalyzer
from app.tools.semgrep_adapter import SemgrepAdapter
from app.tools.bandit_adapter import BanditAdapter
from app.tools.dependency_adapter import DependencyAdapter
from app.tools.android_analyzer import AndroidStaticAnalyzer
from app.tools.cloud_iac_analyzer import CloudIaCAnalyzer
from app.tools.ai_sec_analyzer import AISecAnalyzer
from app.notifications.email_service import EmailService

class MultiAgentOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService(db)

    async def execute_job(self, job_id: str) -> Dict[str, Any]:
        """
        Orchestrates research agents for a given job.
        Strictly follows:
        1. Planning Agent (Scope check & check selection)
        2. Execution Agents (Web, API, Code, Mobile, Cloud, AI Sec)
        3. Correlation Agent (Deduplication & grouping)
        4. Verification Agent (Evidence validation)
        5. Notification & Finalization
        """
        job = self.db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if not job:
            return {"success": False, "error": "Job not found"}

        # Check cancellation
        if job.cancellation_requested:
            job.status = "cancelled"
            self.db.commit()
            return {"success": False, "error": "Job was cancelled before execution."}

        job.status = "running"
        job.started_at = job.started_at or time.strftime("%Y-%m-%d %H:%M:%S")
        self.db.commit()

        # Step 1: Planning Agent & Scope Verification
        is_authorized, scope_msg, scope = validate_target_scope(
            self.db, job.program_id, job.target, requested_method="passive"
        )
        if not is_authorized:
            job.status = "failed"
            job.error_message = f"Planning Agent Scope Rejection: {scope_msg}"
            self.db.commit()
            return {"success": False, "error": job.error_message}

        job.scope_id = scope.id if scope else None
        self.db.commit()

        # Step 2: Execution Agents
        raw_observations = []
        try:
            if job.module_type in ("web", "full_suite"):
                web_agent_results = await self._run_web_agent(job.target)
                raw_observations.extend(web_agent_results)

            if job.module_type in ("code", "full_suite"):
                code_agent_results = await self._run_code_agent(job.target)
                raw_observations.extend(code_agent_results)

            if job.module_type in ("mobile", "full_suite"):
                mobile_agent_results = await self._run_mobile_agent(job.target)
                raw_observations.extend(mobile_agent_results)

            if job.module_type in ("cloud", "full_suite"):
                cloud_agent_results = await self._run_cloud_agent(job.target)
                raw_observations.extend(cloud_agent_results)

            if job.module_type in ("ai_sec", "full_suite"):
                ai_agent_results = await self._run_ai_sec_agent(job.target)
                raw_observations.extend(ai_agent_results)

            # Check if cancellation was requested during execution
            self.db.refresh(job)
            if job.cancellation_requested:
                job.status = "cancelled"
                self.db.commit()
                return {"success": False, "error": "Job cancelled by user request."}

            # Step 3: Correlation Agent
            correlated_findings = self._correlate_findings(job, raw_observations)

            # Step 4: Verification Agent
            verified_findings = self._verify_findings(correlated_findings)

            # Persist findings to database
            high_confidence_detected = False
            for f_data in verified_findings:
                finding = Finding(
                    job_id=job.id,
                    program_id=job.program_id,
                    scope_id=job.scope_id,
                    title=f_data["title"],
                    category=f_data["category"],
                    severity=f_data["severity"],
                    confidence=f_data["confidence"],
                    status=f_data["status"],
                    target=job.target,
                    evidence_summary=f_data.get("evidence", ""),
                    reproduction_steps=f_data.get("reproduction_steps", "Inspect target response or source line indicated in evidence."),
                    impact=f_data.get("impact", ""),
                    remediation=f_data.get("remediation", ""),
                    tool_name=f_data.get("tool_name", "vulnai"),
                    rule_id=f_data.get("rule_id", "vulnai.generic")
                )
                self.db.add(finding)
                self.db.flush() # populate finding.id

                # Store Evidence
                evidence_item = Evidence(
                    finding_id=finding.id,
                    evidence_type="scan_observation",
                    content=f_data.get("evidence", "Observation captured during authorized research run."),
                    request_url=job.target
                )
                self.db.add(evidence_item)

                if finding.confidence in ("Certain", "High") and finding.severity in ("Critical", "High"):
                    high_confidence_detected = True

            job.status = "completed"
            job.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")
            self.db.commit()

            # Step 5: Notifications
            if high_confidence_detected:
                await self.email_service.send_alert(
                    event_type="finding_high_confidence",
                    subject=f"[VulnAI X Alert] High-Confidence Findings Detected on {job.target}",
                    body=f"VulnAI X research job '{job.title}' completed with critical/high confidence findings.\nTarget: {job.target}\nFindings Count: {len(verified_findings)}"
                )

            return {
                "success": True,
                "job_id": job.id,
                "findings_count": len(verified_findings)
            }

        except Exception as e:
            job.status = "failed"
            job.error_message = f"Orchestrator error: {str(e)}"
            self.db.commit()
            return {"success": False, "error": str(e)}

    async def _run_web_agent(self, target: str) -> List[Dict[str, Any]]:
        analyzer = WebPassiveAnalyzer()
        res = await analyzer.scan_target(target)
        self._record_tool_result("web_passive_analyzer", res)
        if res.success:
            return res.structured_data.get("findings", [])
        return []

    async def _run_code_agent(self, target_path: str) -> List[Dict[str, Any]]:
        observations = []
        # Semgrep / SAST
        semgrep = SemgrepAdapter()
        s_res = semgrep.scan_path(target_path)
        self._record_tool_result("semgrep", s_res)
        if s_res.success:
            for r in s_res.structured_data.get("results", []):
                extra = r.get("extra", {})
                observations.append({
                    "title": extra.get("message", "Source Code Issue"),
                    "category": extra.get("category", "Code Security"),
                    "severity": extra.get("severity", "Medium").capitalize(),
                    "confidence": "High",
                    "evidence": f"File: {r.get('path')} (Line {r.get('start', {}).get('line')})\nCode: {extra.get('lines')}",
                    "impact": "Insecure coding practice detected in static source analysis.",
                    "remediation": extra.get("remediation", ""),
                    "tool_name": "semgrep",
                    "rule_id": r.get("check_id")
                })

        # Bandit
        bandit = BanditAdapter()
        if bandit.is_available():
            b_res = bandit.scan_path(target_path)
            self._record_tool_result("bandit", b_res)
            if b_res.success:
                for b in b_res.structured_data.get("results", []):
                    observations.append({
                        "title": b.get("test_name", "Bandit Security Issue"),
                        "category": "Python Security",
                        "severity": b.get("issue_severity", "Medium").capitalize(),
                        "confidence": b.get("issue_confidence", "Medium").capitalize(),
                        "evidence": f"File: {b.get('filename')} (Line {b.get('line_number')})\n{b.get('code', '').strip()}",
                        "impact": b.get("issue_text", ""),
                        "remediation": "Review Python security guidelines and resolve Bandit issue.",
                        "tool_name": "bandit",
                        "rule_id": b.get("test_id")
                    })

        # Dependencies
        dep = DependencyAdapter()
        d_res = dep.scan_path(target_path)
        self._record_tool_result("dependency_audit", d_res)
        if d_res.success:
            for d in d_res.structured_data.get("vulnerabilities", []):
                observations.append({
                    "title": f"Vulnerable Dependency: {d.get('package')} ({d.get('version')})",
                    "category": "Dependency",
                    "severity": d.get("severity", "Medium"),
                    "confidence": "Certain",
                    "evidence": f"Vulnerability ID: {d.get('vuln_id')}\nPackage: {d.get('package')}=={d.get('version')}\nSummary: {d.get('summary')}",
                    "impact": "Using component with known vulnerability (OWASP A06:2021).",
                    "remediation": "Upgrade the affected package to a patched version.",
                    "tool_name": "osv_dependency_audit",
                    "rule_id": d.get("vuln_id")
                })

        return observations

    async def _run_mobile_agent(self, target_path: str) -> List[Dict[str, Any]]:
        analyzer = AndroidStaticAnalyzer()
        res = analyzer.analyze_target(target_path)
        self._record_tool_result("android_static_analyzer", res)
        if res.success:
            return res.structured_data.get("findings", [])
        return []

    async def _run_cloud_agent(self, target_path: str) -> List[Dict[str, Any]]:
        analyzer = CloudIaCAnalyzer()
        res = analyzer.scan_path(target_path)
        self._record_tool_result("cloud_iac_analyzer", res)
        if res.success:
            return res.structured_data.get("findings", [])
        return []

    async def _run_ai_sec_agent(self, target_path: str) -> List[Dict[str, Any]]:
        analyzer = AISecAnalyzer()
        res = analyzer.scan_path(target_path)
        self._record_tool_result("ai_sec_analyzer", res)
        if res.success:
            return res.structured_data.get("findings", [])
        return []

    def _correlate_findings(self, job: ResearchJob, raw_observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicates and merges related observations that share target & title/rule.
        """
        deduped = {}
        for obs in raw_observations:
            key = f"{obs.get('title')}:{obs.get('rule_id')}"
            if key in deduped:
                # Merge evidence
                deduped[key]["evidence"] += f"\n---\nAdditional observation: {obs.get('evidence')}"
            else:
                deduped[key] = obs
        return list(deduped.values())

    def _verify_findings(self, correlated: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Verification Agent:
        Never marks a finding as Verified purely based on AI prediction.
        Only transitions to 'Verified in Authorized Environment' if repeatable evidence exists.
        Otherwise retains status as 'Detected' or 'Needs Investigation'.
        """
        for item in correlated:
            has_evidence = bool(item.get("evidence") and len(item.get("evidence").strip()) > 10)
            confidence = item.get("confidence", "Medium")
            
            if has_evidence and confidence == "Certain":
                item["status"] = "Verified in Authorized Environment"
            elif has_evidence and confidence == "High":
                item["status"] = "Needs Investigation"
            else:
                item["status"] = "Detected"
        return correlated

    def _record_tool_result(self, tool_name: str, res: Any):
        tool_res = ToolResult(
            job_id="", # Assigned by caller or set
            tool_name=tool_name,
            raw_output=res.raw_output[:1000] if hasattr(res, "raw_output") else "",
            structured_json=str(res.structured_data)[:2000] if hasattr(res, "structured_data") else "",
            execution_time_ms=getattr(res, "execution_time_ms", 0),
            exit_code=getattr(res, "exit_code", 0)
        )
