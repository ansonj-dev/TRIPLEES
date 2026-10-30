from __future__ import annotations

from ..ai.structured_output import AgentOutput, FindingOutput
from .common import AgentContext, AgentExecutionResult


class MonitoringAnalyst:
    agent_key = "monitoring_analyst"
    task_summary = "Summarize supplied monitoring records and clearly retain their source and synthetic status."

    def run(self, context: AgentContext) -> AgentExecutionResult:
        observations = context.observations[:200]
        findings = []
        for row in observations:
            observation_id = str(row.get("id") or "")
            evidence_id = str(row.get("evidence_file_id") or "")
            synthetic = bool(row.get("is_synthetic", row.get("synthetic", False)))
            signal = str(row.get("signal_type") or row.get("signal") or "observation")
            severity = str(row.get("severity") or "low").lower()
            if severity not in {"info", "low", "medium", "high", "critical"}:
                severity = "low"
            observed_at = str(row.get("observed_at") or "date not supplied")
            description = str(row.get("description") or row.get("explanation") or "No observation description was supplied.")[:1500]
            qualifier = "Synthetic demonstration" if synthetic else "Supplied"
            refs = [observation_id] if observation_id else []
            evidence_refs = [evidence_id] if evidence_id in context.evidence_ids else []
            findings.append(FindingOutput(
                category="monitoring_signal", severity=severity,
                title=f"{qualifier} monitoring signal: {signal.replace('_', ' ')}"[:300],
                description=f"{qualifier} observation dated {observed_at}: {description} This is a signal requiring review, not confirmation of environmental damage or carbon reversal.",
                evidence_ids=evidence_refs, source_ids=refs,
                confidence=0.2 if synthetic else 0.45,
                status="hypothesis" if synthetic else "requires_human_review",
                basis="observation",
                recommendation="Check the original source, time period, spatial coverage, and supporting evidence with a qualified reviewer.",
            ))
        limitations = ["No live satellite, remote-sensing, or IoT feed was queried.", "A missing observation in this input is not evidence that no environmental change occurred."]
        if not observations:
            findings.append(FindingOutput(
                category="data_gap", severity="info", title="No monitoring observations supplied",
                description="No monitoring observations were included in this run. Coverage and environmental conditions cannot be inferred from this absence.",
                confidence=1.0, status="unresolved", basis="unresolved",
                recommendation="Provide observations with source, timestamp, measurement, and coverage metadata.",
            ))
        state = "completed_with_limitations"
        return AgentExecutionResult(
            self.agent_key, state, self.task_summary,
            AgentOutput(summary=f"Reviewed {len(observations)} supplied monitoring observation(s).", findings=findings, limitations=limitations),
        )
