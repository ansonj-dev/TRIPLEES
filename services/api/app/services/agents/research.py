from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from urllib.parse import urlsplit

from ..ai.structured_output import AgentOutput
from .common import AgentContext, AgentExecutionResult, safe_public_https_url


class PublicResearchProvider(Protocol):
    provider_name: str

    def search(self, query: str, *, max_results: int) -> list[dict[str, str]]:
        """Search public sources and return factual metadata with source URLs."""
        ...


class UnconfiguredResearchProvider:
    provider_name = "unconfigured"

    def search(self, _query: str, *, max_results: int) -> list[dict[str, str]]:
        return []


class ResearchInvestigator:
    agent_key = "research_investigator"
    task_summary = "Check whether public-source research is available and retain references without inventing citations."

    def __init__(self, provider: PublicResearchProvider | None = None):
        self.provider = provider or UnconfiguredResearchProvider()

    @staticmethod
    def _safe_public_url(value: str) -> bool:
        return safe_public_https_url(value)

    def run(self, context: AgentContext) -> AgentExecutionResult:
        project_name = str(context.project.get("name") or "the selected project")
        if not context.public_research_authorized:
            return AgentExecutionResult(
                self.agent_key, "completed_with_limitations", self.task_summary,
                AgentOutput(summary="External public-source research was not performed.", limitations=["Public web research was not authorized for this run."]),
                "public_research_not_authorized",
            )
        if self.provider.provider_name == "unconfigured":
            supplied = [row for row in context.source_references if row.get("url") and row.get("title") and self._safe_public_url(str(row.get("url")))]
            output = AgentOutput(
                summary=f"No external search provider is configured. {len(supplied)} source reference(s) were already present in the supplied context.",
                sources=[{key: str(value) for key, value in row.items() if value is not None and key in {"id", "title", "url", "publisher", "domain", "retrieved_at", "published_at", "excerpt"}} for row in supplied[:40]],
                limitations=["External research was not performed; supplied references were not independently fetched or verified."],
            )
            return AgentExecutionResult(self.agent_key, "completed_with_limitations", self.task_summary, output, "research_provider_not_configured")
        try:
            results = self.provider.search(f'"{project_name}" carbon project registry methodology', max_results=10)
        except Exception:
            return AgentExecutionResult(self.agent_key, "failed", self.task_summary, error_code="research_provider_error")
        safe = []
        limitations = ["Search results are leads, not conclusive evidence; verify the original publisher and source content."]
        for row in results[:10]:
            if not isinstance(row, dict):
                limitations.append("One or more results were excluded because source metadata was not structured.")
                continue
            url = str(row.get("url") or "")
            if not self._safe_public_url(url) or not row.get("title"):
                limitations.append("One or more results were excluded because source metadata or a safe public HTTPS URL was missing.")
                continue
            parts = urlsplit(url)
            if len(url) > 2_000:
                limitations.append("One or more results were excluded because the URL exceeded the supported length.")
                continue
            source = {key: str(value)[:2_000] for key, value in row.items() if value is not None and key in {"title", "publisher", "url", "published_at", "excerpt"}}
            source["title"] = source["title"][:300]
            for key in ("publisher", "published_at"):
                if key in source:
                    source[key] = source[key][:200 if key == "publisher" else 40]
            source["domain"] = parts.hostname or ""
            source["retrieved_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            safe.append(source)
        output = AgentOutput(
            summary=f"Retrieved {len(safe)} public reference(s) for human verification.",
            sources=safe,
            limitations=list(dict.fromkeys(limitations)),
        )
        return AgentExecutionResult(self.agent_key, "completed", self.task_summary, output, provider=self.provider.provider_name)
