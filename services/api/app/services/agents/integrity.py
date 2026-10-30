from __future__ import annotations

from collections import defaultdict

from ..ai.structured_output import AgentOutput, FindingOutput
from .common import AgentContext, AgentExecutionResult


class IntegrityAnalyst:
    agent_key = "integrity_analyst"
    task_summary = "Compare only the supplied project identifiers and imported registry rows."

    def run(self, context: AgentContext) -> AgentExecutionResult:
        records = context.registry_records[:200]
        findings: list[FindingOutput] = []
        by_serial: dict[str, list[dict]] = defaultdict(list)
        for row in records:
            serial = str(row.get("external_serial") or row.get("serial") or "").strip().casefold()
            if serial:
                by_serial[serial].append(row)
        for serial, rows in by_serial.items():
            if len(rows) < 2:
                continue
            refs = [str(row["id"]) for row in rows if row.get("id")]
            sources = ", ".join(str(row.get("source_name") or "unnamed import") for row in rows[:4])
            findings.append(FindingOutput(
                category="registry_inconsistency", severity="high",
                title="Duplicate serial in imported records",
                description=f"The supplied import set contains serial {serial!r} more than once ({sources}). This identifies a record conflict in the available data; it does not prove duplicate issuance, fraud, or an invalid credit.",
                claim="The supplied registry imports contain one row per serial.",
                observed_value=f"{len(rows)} rows share this normalized serial.",
                source_ids=refs, confidence=1.0, status="requires_human_review", basis="record_fact",
                recommendation="Compare the original registry records and confirm project and serial-range identity.",
            ))
            quantities = {row.get("quantity_kg_co2e", row.get("quantity")) for row in rows if row.get("quantity_kg_co2e", row.get("quantity")) is not None}
            if len(quantities) > 1:
                findings.append(FindingOutput(
                    category="quantity_mismatch", severity="high",
                    title="Conflicting quantities for an imported serial",
                    description=f"Rows sharing serial {serial!r} report different quantities. The import set may be incomplete or inconsistent; reconcile against the original sources.",
                    observed_value=", ".join(sorted(str(value) for value in quantities)),
                    source_ids=refs, confidence=1.0, status="requires_human_review", basis="record_fact",
                    recommendation="Request authoritative registry documentation for the quantity and unit.",
                ))
        project_ref = str(context.project.get("registry_project_ref") or "").strip().casefold()
        project_id = str(context.project.get("id") or "").strip().casefold()
        project_name = str(context.project.get("name") or "").strip().casefold()
        project_rows = [row for row in records if any(
            value and str(value).strip().casefold() in {project_ref, project_id, project_name}
            for value in (row.get("external_project_id"), row.get("project_id"), row.get("external_project_name"), row.get("project_name"))
        )]
        if project_rows:
            quantities = {row.get("quantity_kg_co2e", row.get("quantity")) for row in project_rows if row.get("quantity_kg_co2e", row.get("quantity")) is not None}
            if len(quantities) > 1 and not any(f.category == "quantity_mismatch" for f in findings):
                findings.append(FindingOutput(
                    category="quantity_mismatch", severity="medium",
                    title="Project-linked import quantities differ",
                    description="Imported rows matching the supplied project reference contain more than one quantity. The imported sources may describe different vintages or scopes.",
                    observed_value=", ".join(sorted(str(value) for value in quantities)),
                    source_ids=[str(row["id"]) for row in project_rows if row.get("id")],
                    confidence=0.8, status="requires_human_review", basis="record_fact",
                    recommendation="Confirm the registry scope, vintage, serial range, and quantity units before comparing totals.",
                ))
        limitations = ["Checks cover only the registry rows provided to this agent; no external registry was queried.", "Serial matching is normalized exact text matching; registry serial-range semantics are not inferred."]
        if not records:
            findings.append(FindingOutput(
                category="data_gap", severity="info", title="No registry rows available for comparison",
                description="No imported registry records were supplied for this project comparison. This does not establish that no external registry records exist.",
                confidence=1.0, status="unresolved", basis="unresolved",
                recommendation="Import or connect authoritative registry records before drawing a comparison.",
            ))
        return AgentExecutionResult(
            self.agent_key, "completed_with_limitations", self.task_summary,
            AgentOutput(summary=f"Compared {len(records)} supplied registry row(s) with exact normalized serial and available project references.", findings=findings, limitations=limitations),
        )
