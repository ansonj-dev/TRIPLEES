from __future__ import annotations

import hashlib
import uuid
from datetime import timedelta

import pytest
from sqlalchemy import create_engine, event
from fastapi.testclient import TestClient

from services.api.app import config as app_config
from services.api.app import db as app_db
from services.api.app import main as app_main
from services.api.app import storage as app_storage
from services.api.app import report_anchor_routes as app_report_anchor_routes
from services.api.app.main import app
from services.api.app.models import ModelUsage, utcnow
from services.api.app.models import AgentAuditEvent, AgentExecution, AgentFinding, Investigation


def test_investigation_lifecycle_and_worker_resume(isolated_backend, monkeypatch):
    from services.api.worker import claim_next_job, process_job
    from services.api.app.services.agents.common import AgentExecutionResult
    from services.api.app.services.ai.structured_output import AgentOutput, FindingOutput, SourceOutput

    class FakeAgent:
        task_summary = "A deterministic fixture agent."

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)

        def run(self, _context):
            return AgentExecutionResult(
                self.agent_key, "completed", self.task_summary,
                AgentOutput(summary=f"{self.agent_key} fixture output.", findings=[FindingOutput(
                    category="fixture", severity="info", title="Fixture finding",
                    description="A scoped test fixture finding.", evidence_ids=[], source_ids=[],
                    confidence=0.5, status="unresolved", basis="unresolved",
                )]),
            )

    class Evidence(FakeAgent):
        agent_key = "evidence_analyst"
        calls = 0

        def run(self, context):
            type(self).calls += 1
            if type(self).calls == 1:
                return AgentExecutionResult(self.agent_key, "failed", self.task_summary, error_code="fixture_transient")
            return super().run(context)

    class Integrity(FakeAgent):
        agent_key = "integrity_analyst"

    class Research(FakeAgent):
        agent_key = "research_investigator"

        def run(self, _context):
            return AgentExecutionResult(self.agent_key, "completed_with_limitations", self.task_summary, AgentOutput(
                summary="Local research output fixture.",
                findings=[FindingOutput(
                    category="source_check", severity="medium", title="Public source needs review",
                    description="A source is provided for a local persistence test.", source_ids=["source-fixture"],
                    confidence=0.5, status="requires_human_review", basis="record_fact",
                )],
                sources=[SourceOutput(id="source-fixture", title="Registry record", url="https://registry.example.org/project/1",
                                      publisher="Example Registry", domain="registry.example.org", retrieved_at="2026-10-30T00:00:00Z")],
                limitations=["This is a local source fixture, not externally fetched."],
            ))

    class Monitoring(FakeAgent):
        agent_key = "monitoring_analyst"

    class Review(FakeAgent):
        agent_key = "independent_review_agent"

        def run(self, _context, _drafts):
            return AgentExecutionResult(self.agent_key, "completed", self.task_summary, AgentOutput(summary="Review fixture output."))

    suite = (Evidence, Integrity, Research, Monitoring, Review)
    with TestClient(app) as client:
        token = client.post("/api/auth/demo").json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "phase4-investigation-1"}
        project = client.post("/api/projects", headers=headers, json={
            "name": "Persistent job test", "project_type": "forest", "country": "Kenya",
        }).json()
        payload = {
            "project_id": project["id"], "title": "Lifecycle check", "scope": "Check only this project.",
            "evidence_ids": [], "external_ai_authorized": False, "public_research_authorized": False,
            "ai_token_budget": 0,
        }
        created = client.post("/api/investigations", headers=headers, json=payload)
        assert created.status_code == 201
        investigation_id = created.json()["id"]
        repeated = client.post("/api/investigations", headers=headers, json=payload)
        assert repeated.status_code == 200
        assert repeated.json()["id"] == investigation_id
        conflict = client.post("/api/investigations", headers=headers, json={**payload, "title": "Different payload"})
        assert conflict.status_code == 409
        assert client.get(f"/api/investigations/{investigation_id}", headers=headers).status_code == 200
        queued = client.post(f"/api/investigations/{investigation_id}/run", headers=headers)
        assert queued.status_code == 202

        worker_id = "test-worker"
        assert claim_next_job(worker_id) == investigation_id
        process_job(investigation_id, worker_id, suite)

        result = client.get(f"/api/investigations/{investigation_id}", headers=headers).json()
        assert result["status"] == "completed_with_limitations"
        assert len(result["executions"]) == 6
        assert [x["status"] for x in result["executions"][:2]] == ["failed", "completed"]
        assert result["executions"][-1]["output"]["summary"] == "Review fixture output."
        findings_result = client.get(f"/api/investigations/{investigation_id}/findings", headers=headers)
        assert findings_result.status_code == 200
        assert findings_result.json()["total"] == 4
        global_findings = client.get("/api/findings?limit=200", headers=headers)
        assert global_findings.status_code == 200
        assert global_findings.json()["total"] == 4
        cited = next(item for item in findings_result.json()["items"] if item["category"] == "source_check")
        assert cited["status"] == "requires_human_review"
        assert cited["sources"][0]["url"] == "https://registry.example.org/project/1"
        developer = client.post("/api/auth/signup", json={
            "display_name": "Other Investigator", "email": "other-investigator@example.invalid",
            "password": "LongEnoughPassword2026!",
        }).json()
        other_headers = {"Authorization": f"Bearer {developer['access_token']}"}
        assert client.get("/api/findings?limit=200", headers=other_headers).json()["total"] == 0
        assert client.get(f"/api/investigations/{investigation_id}/report", headers=other_headers).status_code == 404
        assert client.post(f"/api/findings/{cited['id']}/review", headers=other_headers, json={
            "decision": "confirmed", "reason": "This user must not review the finding.",
        }).status_code == 403
        reports = client.get(f"/api/investigations/{investigation_id}/report", headers=headers)
        assert reports.status_code == 200
        assert reports.json()["version"] == 1
        assert reports.json()["available_versions"] == [1]
        assert reports.json()["content"]["findings"]
        assert len(reports.json()["commitment"]["sha256"]) == 64
        report_id = reports.json()["id"]
        approval = client.post(
            f"/api/investigations/{investigation_id}/reports/{report_id}/anchor/approve",
            headers=headers, json={"reason": "Reviewed this immutable report snapshot and its digest."},
        )
        assert approval.status_code == 200
        assert approval.json()["status"] == "approved"
        assert approval.json()["sha256"] == reports.json()["commitment"]["sha256"]
        anchor_id = approval.json()["id"]
        public_anchor = client.get(f"/api/public/report-anchors/{anchor_id}")
        assert public_anchor.status_code == 200
        assert public_anchor.json()["sha256"] == approval.json()["sha256"]
        assert "content" not in public_anchor.json() and "summary" not in public_anchor.json()
        assert client.post(f"/api/report-anchors/{anchor_id}/submit", headers=headers, json={"confirm_submission": False}).status_code == 422
        assert client.post(
            f"/api/investigations/{investigation_id}/reports/{report_id}/anchor/approve",
            headers=other_headers, json={"reason": "This user cannot approve a report anchor."},
        ).status_code == 403
        class ValueCall:
            def __init__(self, getter): self.getter = getter
            def call(self): return self.getter()

        class FakeAnchorFunctions:
            def __init__(self): self.record = None
            def isAnchored(self, _key): return ValueCall(lambda: self.record is not None)
            def getReportAnchor(self, _key): return ValueCall(lambda: self.record or (False, bytes(32), 0, "0x" + "00" * 20, 0))
            def anchorReport(self, _key, digest, version):
                return ValueCall(lambda: setattr(self, "record", (True, digest, version, "0x" + "11" * 20, 1793600000)))

        class FakeContract:
            address = "0x" + "22" * 20
            def __init__(self): self.functions = FakeAnchorFunctions()

        fake_contract = FakeContract()
        class FakeEth:
            def get_block(self, _block): return type("Block", (), {"timestamp": 1793600000})()

        class FakeClient:
            def __init__(self): self.w3 = type("FakeWeb3", (), {"eth": FakeEth()})()
            def report_anchor_contract(self): return fake_contract
            def role_account(self, role):
                assert role == "reviewer"
                return type("FakeAccount", (), {"address": "0x" + "33" * 20})()
            def send_contract_transaction(self, role, function, contract=None, on_broadcast=None):
                assert role == "reviewer" and contract is fake_contract
                if on_broadcast: on_broadcast("0x" + "cc" * 32)
                function.call()
                return {"status": "confirmed", "transaction_hash": "0x" + "cc" * 32,
                        "block_number": 123, "contract_address": fake_contract.address}

        monkeypatch.setattr(app_report_anchor_routes, "X1ChainClient", FakeClient)
        submitted = client.post(f"/api/report-anchors/{anchor_id}/submit", headers=headers, json={"confirm_submission": True})
        assert submitted.status_code == 200
        assert submitted.json()["status"] == "confirmed"
        assert submitted.json()["transaction_hash"] == "0x" + "cc" * 32
        assert submitted.json()["chain_id"] == 10778
        assert client.post(f"/api/report-anchors/{anchor_id}/submit", headers=headers, json={"confirm_submission": True}).json()["status"] == "confirmed"
        reconciled = client.post(f"/api/report-anchors/{anchor_id}/reconcile", headers=headers)
        assert reconciled.status_code == 200 and reconciled.json()["verified_on_chain"] is True
        verified_public = client.get(f"/api/public/report-anchors/{anchor_id}").json()
        assert verified_public["verified_on_chain"] is True
        assert "content" not in verified_public and "investigation_id" not in verified_public
        assert any("fixture" in item.lower() for item in reports.json()["limitations"])
        sources = client.get(f"/api/investigations/{investigation_id}/sources", headers=headers)
        assert len(sources.json()["items"]) == 1
        assert client.get(f"/api/investigations/{investigation_id}/agents", headers=headers).status_code == 200
        review = client.post(f"/api/findings/{cited['id']}/review", headers=headers, json={
            "decision": "confirmed", "reason": "I verified the citation and supporting registry record.",
        })
        assert review.status_code == 200
        assert review.json()["report_version"] == 2
        assert client.get(f"/api/investigations/{investigation_id}/findings?review_decision=confirmed", headers=headers).json()["total"] == 1
        assert client.get("/api/findings/review-queue", headers=headers).json()["total"] == 3
        assert client.get("/api/findings/review-queue", headers=other_headers).status_code == 403
        report_v1 = client.get(f"/api/investigations/{investigation_id}/report?version=1", headers=headers).json()
        report_v2 = client.get(f"/api/investigations/{investigation_id}/report?version=2", headers=headers).json()
        assert report_v1["content"]["findings"] != report_v2["content"]["findings"]
        reviewed_finding = next(item for item in report_v2["content"]["findings"] if item["id"] == cited["id"])
        assert reviewed_finding["reviews"][0]["decision"] == "confirmed"
        assert report_v2["available_versions"] == [2, 1]
        audit = client.get(f"/api/investigations/{investigation_id}/audit", headers=headers).json()["items"]
        assert any(item["event_type"] == "worker_job_claimed" for item in audit)
        assert any(item["event_type"] == "investigation_finished" for item in audit)
        assert any(item["event_type"] == "finding_reviewed" for item in audit)
        assert any(item["event_type"] == "report_anchor_approved" for item in audit)
        assert any(item["event_type"] == "report_anchor_confirmed" for item in audit)

        with app_db.SessionLocal() as db:
            assert db.query(AgentExecution).filter_by(investigation_id=investigation_id).count() == 6
            assert db.query(AgentAuditEvent).filter_by(investigation_id=investigation_id).count() >= 19
            assert db.query(AgentFinding).filter_by(investigation_id=investigation_id).count() == 4
            assert db.query(Investigation).filter_by(id=investigation_id).one().ai_tokens_used == 0

        cancel_project = client.post("/api/projects", headers=headers, json={
            "name": "Cancel job test", "project_type": "forest", "country": "Kenya",
        }).json()
        cancel = client.post("/api/investigations", headers={"Authorization": f"Bearer {token}"}, json={
            "project_id": cancel_project["id"], "title": "Cancel check", "scope": "Cancel before processing.",
        }).json()
        cancel_response = client.post(f"/api/investigations/{cancel['id']}/cancel", headers={"Authorization": f"Bearer {token}"})
        assert cancel_response.json()["status"] == "cancelled"

        stale = client.post("/api/investigations", headers={"Authorization": f"Bearer {token}"}, json={
            "project_id": cancel_project["id"], "title": "Lease recovery check", "scope": "Recover an expired worker lease.",
        }).json()
        with app_db.SessionLocal() as db:
            row = db.get(Investigation, stale["id"])
            row.status = "running"
            row.attempt_count = 1
            row.worker_id = "dead-worker"
            row.lease_expires_at = utcnow() - timedelta(seconds=1)
            db.add(AgentExecution(
                id="EXE-stale-test", investigation_id=row.id, agent_key="evidence_analyst",
                attempt_number=1, status="running", task_summary="Interrupted fixture execution.", worker_id="dead-worker",
                started_at=utcnow() - timedelta(minutes=4),
            ))
            db.commit()
        from services.api.worker import recover_expired_leases
        with app_db.SessionLocal() as db:
            assert recover_expired_leases(db) == 1
            recovered = db.get(Investigation, stale["id"])
            interrupted = db.get(AgentExecution, "EXE-stale-test")
            assert recovered.status == "retry_wait"
            assert interrupted.status == "failed"
            assert interrupted.error_code == "worker_lease_expired"


def test_investigation_rejects_evidence_from_another_project(isolated_backend):
    with TestClient(app) as client:
        token = client.post("/api/auth/demo").json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        project_ids = []
        for name in ("Investigation project A", "Investigation project B"):
            response = client.post("/api/projects", headers=headers, json={
                "name": name, "project_type": "forest", "country": "Kenya",
            })
            project_ids.append(response.json()["id"])
        evidence = client.post(
            f"/api/projects/{project_ids[1]}/evidence", headers=headers,
            files={"file": ("evidence.txt", b"Evidence for project B.", "text/plain")},
            data={"evidence_type": "document"},
        ).json()
        result = client.post("/api/investigations", headers=headers, json={
            "project_id": project_ids[0], "title": "Boundary check", "scope": "Do not cross project boundary.",
            "evidence_ids": [evidence["id"]],
        })
        assert result.status_code == 422


def test_daily_ai_token_limit_uses_rolling_user_usage(isolated_backend, monkeypatch):
    from services.api.worker import daily_ai_token_limit_reached

    monkeypatch.setattr(app_config, "AI_DAILY_TOKEN_LIMIT", 100)
    app_main.seed_database()
    with app_db.SessionLocal() as db:
        db.add(ModelUsage(
            id="USG-DAILY-LIMIT", requested_by="demo-reviewer", provider="fixture",
            model_name="fixture", input_tokens=70, output_tokens=20, latency_ms=1,
            succeeded=True, created_at=utcnow(),
        ))
        db.commit()
        assert daily_ai_token_limit_reached(db, "demo-reviewer", 11) == (True, 90)
        assert daily_ai_token_limit_reached(db, "demo-reviewer", 10) == (False, 90)


@pytest.fixture
def isolated_backend(tmp_path, monkeypatch):
    """Keep workflow tests away from the developer's real SQLite workspace."""
    original_engine = app_db.engine
    original_storage_dir = app_storage.UPLOAD_DIR
    test_db = tmp_path / "vericarb-test.sqlite3"
    database_url = f"sqlite:///{test_db.as_posix()}"
    upload_dir = tmp_path / "evidence"
    upload_dir.mkdir()
    test_engine = create_engine(database_url, connect_args={"check_same_thread": False}, pool_pre_ping=True)

    @event.listens_for(test_engine, "connect")
    def enable_test_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    app_db.engine = test_engine
    app_db.SessionLocal.configure(bind=test_engine)
    app_db.Base.metadata.create_all(bind=test_engine)
    monkeypatch.setattr(app_config, "DATABASE_URL", database_url)
    monkeypatch.setattr(app_storage, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(app_main, "AUTO_MIGRATE", False)
    monkeypatch.setenv("X1_REGISTRY_CONTRACT_ADDRESS", "")
    try:
        yield
    finally:
        app_db.SessionLocal.configure(bind=original_engine)
        app_db.engine = original_engine
        monkeypatch.setattr(app_storage, "UPLOAD_DIR", original_storage_dir)
        test_engine.dispose()


def test_frontend_assets_and_static_boundary():
    client = TestClient(app)
    public_paths = (
        "/", "/index.html", "/auth.html", "/app.html", "/verify.html", "/report-verify.html",
        "/assets/css/app.css", "/assets/css/auth.css", "/assets/css/styles.css",
        "/assets/css/public-ui.css", "/assets/css/workspace-ui.css",
        "/assets/js/app.js", "/assets/js/auth.js", "/assets/js/public-verify.js", "/assets/js/report-verify.js",
        "/assets/js/script.js", "/assets/images/favicon.svg",
    )
    for path in public_paths:
        assert client.get(path).status_code == 200, path
    private_paths = (
        "/.env", "/.env.example", "/.git/config", "/README.md",
        "/services/api/app/main.py", "/data/vericarb.sqlite3",
        "/sample-data/demo_project.json", "/tools/demo-video/package.json",
    )
    for path in private_paths:
        assert client.get(path).status_code == 404, path


def test_demo_access_uses_token_endpoint_without_exposing_a_password(isolated_backend):
    with TestClient(app) as client:
        response = client.post("/api/auth/demo")
        assert response.status_code == 200
        headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        assert client.get("/api/me", headers=headers).json()["id"] == "demo-reviewer"
        assert client.post("/api/auth/login", json={"email": "demo@example.invalid", "password": "not-a-demo-password"}).status_code == 401
        with app_db.SessionLocal() as db:
            demo = db.get(app_main.Profile, "demo-reviewer")
            demo.password_salt = None
            demo.password_hash = None
            db.commit()
        app_main.seed_database()
        assert client.post("/api/auth/login", json={"email": "demo@example.invalid", "password": "not-a-demo-password"}).status_code == 401


def test_api_workflows(isolated_backend):
    """Exercise local auth, persisted project/evidence, reviewer, and lifecycle rules."""
    # The application reads its DB URL at import time; this test suite uses the
    # same local prototype database as startup so the migration path is covered.
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"
        assert client.get("/api/dashboard").status_code == 401
        public_network = client.get("/api/blockchain/network")
        assert public_network.status_code == 200
        assert public_network.json()["expected_chain_id"] == 10778
        assert "error" in public_network.json()

        auth = client.post("/api/auth/demo").json()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        chain_status = client.get("/api/blockchain/status", headers=headers)
        assert chain_status.status_code == 200
        assert all("private_key" not in wallet for wallet in chain_status.json()["wallets"])
        assert client.get("/api/blockchain/contracts", headers=headers).status_code == 200
        assert client.get("/api/blockchain/wallets/not-an-address/balance", headers=headers).status_code == 422
        client.post("/api/demo/reset", headers=headers)
        assert client.get("/api/demo/bootstrap", headers=headers).status_code == 200

        created = client.post("/api/projects", headers=headers, json={
            "name": "Acceptance test forest", "project_type": "forest", "country": "Kenya",
            "region": "Central", "methodology_id": "TEST-METHODOLOGY",
        })
        assert created.status_code == 201
        project_id = created.json()["id"]
        assert client.get(f"/api/projects/{project_id}", headers=headers).status_code == 200

        payload = b"synthetic evidence fixture\n"
        uploaded = client.post(
            f"/api/projects/{project_id}/evidence", headers=headers,
            files={"file": ("evidence.txt", payload, "text/plain")},
            data={"evidence_type": "document", "source_name": "pytest fixture"},
        )
        assert uploaded.status_code == 201
        assert uploaded.json()["sha256"] == hashlib.sha256(payload).hexdigest()
        assert client.post(f"/api/projects/{project_id}/evidence", headers=headers, data={"evidence_type": "unknown"}, files={"file": ("bad.txt", b"x", "text/plain")}).status_code == 422
        assert client.post(
            f"/api/projects/{project_id}/evidence", headers=headers,
            files={"file": ("payload.exe", b"bad", "application/octet-stream")},
        ).status_code == 415

        assessment = client.post("/api/assessments/evidence-review", headers=headers, json={"evidence_id": uploaded.json()["id"]})
        assert assessment.status_code == 201
        assert assessment.json()["automatic_approval"] is False
        decision = client.post(f"/api/assessments/{assessment.json()['id']}/review", headers=headers, json={"decision": "approved", "reason": "Reviewed deterministic findings"})
        assert decision.status_code == 201

        draft = client.post(f"/api/projects/{project_id}/batches", headers=headers, json={
            "serial_start": "TEST-SERIAL-001", "quantity_kg_co2e": 1000,
        })
        assert draft.status_code == 201
        batch_id = draft.json()["id"]
        assert client.post(f"/api/batches/{batch_id}/submit", headers=headers, json={"reason": "Ready for review"}).status_code == 200
        reviewed = client.post(f"/api/batches/{batch_id}/review", headers=headers, json={"decision": "approved", "reason": "Evidence reviewed for demo"})
        assert reviewed.status_code == 201
        issued = client.post(f"/api/batches/{batch_id}/issue", headers=headers, json={"reason": "Local demo issuance"})
        assert issued.status_code == 200
        assert issued.json()["transaction"]["status"] == "not_configured"

        overdraw = client.post(f"/api/batches/{batch_id}/retire", headers=headers, json={
            "quantity_kg_co2e": 1001, "beneficiary": "Example", "purpose": "Test", "reason": "Overdraw should fail",
        })
        assert overdraw.status_code == 409
        retired = client.post(f"/api/batches/{batch_id}/retire", headers=headers, json={
            "quantity_kg_co2e": 400, "beneficiary": "Example", "purpose": "Test", "reason": "Partial demo retirement",
        })
        assert retired.status_code == 200
        assert retired.json()["retired_balance_kg"] == 400
        assert retired.json()["available_balance_kg"] == 600

        public = client.get(f"/api/public/verify/{draft.json()['batch_code']}")
        assert public.status_code == 200
        assert client.get("/verify.html").status_code == 200
        assert "filename" not in public.json()["public_evidence"][0]
        assert "storage_key" not in public.json()["batch"]
        assert public.json()["batch"]["retired_balance_kg"] == 400
        assert all("reason" not in event for event in public.json()["events"])


def test_auth_signup_login_and_role_boundary():
    with TestClient(app) as client:
        email = f"api-test-{uuid.uuid4().hex}@example.invalid"
        signup = client.post("/api/auth/signup", json={
            "display_name": "API Test", "email": email, "password": "LocalDemoPassphrase!",
        })
        assert signup.status_code == 201
        token = signup.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/me", headers=user_headers).json()["email"] == email
        assert client.post("/api/auth/login", json={"email": email, "password": "wrong"}).status_code == 401
        assert client.post("/api/auth/login", json={"email": email, "password": "LocalDemoPassphrase!"}).status_code == 200
        assert client.post("/api/alerts/ALT-DEMO-001/review", headers=user_headers, json={"decision": "alert_rejected", "reason": "Role boundary check"}).status_code == 403


def test_ai_health_and_usage_are_authenticated_and_redacted(isolated_backend):
    with TestClient(app) as client:
        assert client.get("/api/ai/health").status_code == 401
        auth = client.post("/api/auth/demo").json()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        health = client.get("/api/ai/health", headers=headers)
        assert health.status_code == 200
        assert health.json()["provider"] == "nebius_token_factory"
        assert health.json()["configured"] is False
        assert "api_key" not in health.json()
        with app_db.SessionLocal() as db:
            db.add(ModelUsage(
                id="USG-TEST-1", requested_by="demo-reviewer", provider="nebius_token_factory",
                model_name="nvidia/nemotron-3-super-120b-a12b", input_tokens=10, output_tokens=5,
                latency_ms=123, succeeded=True, created_at=utcnow(),
            ))
            db.commit()
        usage = client.get("/api/ai/usage", headers=headers)
        assert usage.status_code == 200
        assert usage.json()["summary"]["input_tokens"] == 10
        assert usage.json()["items"][0]["cost_state"] == "rate_not_configured"


def test_document_extraction_tracks_claim_provenance_and_reuses_identical_hash(isolated_backend):
    with TestClient(app) as client:
        readiness = client.get("/readyz", headers={"X-Request-ID": "phase8-smoke-1"})
        assert readiness.status_code == 200
        assert readiness.json()["evidence_storage"] == "connected"
        assert readiness.headers["x-request-id"] == "phase8-smoke-1"
        auth = client.post("/api/auth/demo").json()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        project = client.post("/api/projects", headers=headers, json={
            "name": "Document extraction test", "project_type": "forest", "country": "Kenya",
        }).json()
        body = b"The project claims 1,250 tCO2e removed during 2024.\nA reviewer should confirm the source.\n"
        first_upload = client.post(
            f"/api/projects/{project['id']}/evidence", headers=headers,
            files={"file": ("claims.txt", body, "text/plain")},
        )
        assert first_upload.status_code == 201
        evidence_id = first_upload.json()["id"]
        assert first_upload.json()["sha256"] == hashlib.sha256(body).hexdigest()
        downloaded = client.get(f"/api/evidence/{evidence_id}/download", headers=headers)
        assert downloaded.status_code == 200
        assert downloaded.content == body
        assert downloaded.headers["content-disposition"].endswith("claims.txt")

        extracted = client.post(f"/api/evidence/{evidence_id}/extract", headers=headers)
        assert extracted.status_code == 200
        assert extracted.json()["status"] == "complete"
        assert extracted.json()["chunk_count"] >= 1
        assert extracted.json()["candidate_claim_count"] == 1
        details = client.get(f"/api/evidence/{evidence_id}/extraction", headers=headers).json()
        assert details["claims"][0]["method"] == "heuristic_candidate"
        assert details["claims"][0]["confidence"] == 0.25
        assert details["claims"][0]["source_location"] == "line 1"
        assert details["claims"][0]["evidence_sha256"] == first_upload.json()["sha256"]
        chunks = client.get(f"/api/evidence/{evidence_id}/extraction/chunks", headers=headers).json()["items"]
        assert chunks[0]["source_location"] == "line 1"
        search = client.get("/api/evidence/search", params={"project_id": project["id"], "q": "1,250"}, headers=headers)
        assert search.status_code == 200
        assert search.json()["items"][0]["evidence_sha256"] == first_upload.json()["sha256"]

        repeated = client.post(f"/api/evidence/{evidence_id}/extract", headers=headers).json()
        assert repeated["id"] == extracted.json()["id"]
        assert repeated["chunk_count"] == extracted.json()["chunk_count"]

        duplicate = client.post(
            f"/api/projects/{project['id']}/evidence", headers=headers,
            files={"file": ("duplicate.txt", body, "text/plain")},
        ).json()
        duplicate_extract = client.post(f"/api/evidence/{duplicate['id']}/extract", headers=headers)
        assert duplicate_extract.status_code == 200
        assert duplicate_extract.json()["reused"] is True
        assert duplicate_extract.json()["reused_from_id"] == extracted.json()["id"]

        with app_db.SessionLocal() as db:
            row = db.get(app_main.EvidenceFile, evidence_id)
            (app_storage.UPLOAD_DIR / row.storage_key).write_bytes(b"tampered after upload")
        tampered = client.post(f"/api/evidence/{evidence_id}/extract", headers=headers)
        assert tampered.status_code == 409
        assert tampered.json()["detail"]["code"] == "evidence_hash_mismatch"

        other_user = client.post("/api/auth/signup", json={
            "display_name": "Other owner", "email": f"other-{uuid.uuid4().hex}@example.invalid",
            "password": "AnotherLocalPassphrase!",
        }).json()
        other_headers = {"Authorization": f"Bearer {other_user['access_token']}"}
        assert client.get(f"/api/evidence/{evidence_id}/extraction", headers=other_headers).status_code == 404


def test_document_extraction_preserves_csv_json_and_pdf_locations(isolated_backend):
    import pymupdf

    with TestClient(app) as client:
        auth = client.post("/api/auth/demo").json()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        project = client.post("/api/projects", headers=headers, json={
            "name": "Source location test", "project_type": "forest", "country": "Kenya",
        }).json()

        csv_upload = client.post(
            f"/api/projects/{project['id']}/evidence", headers=headers,
            files={"file": ("registry.csv", b"project,quantity\nForest Alpha,100 tCO2e\n", "text/csv")},
        ).json()
        csv_result = client.post(f"/api/evidence/{csv_upload['id']}/extract", headers=headers).json()
        assert csv_result["status"] == "complete"
        csv_claims = client.get(f"/api/evidence/{csv_upload['id']}/extraction", headers=headers).json()["claims"]
        assert csv_claims[0]["source_location"] == "row 2"

        json_body = b'{"project":{"name":"Forest Beta","claim":"The project claims 250 tCO2e."}}'
        json_upload = client.post(
            f"/api/projects/{project['id']}/evidence", headers=headers,
            files={"file": ("project.json", json_body, "application/json")},
        ).json()
        json_result = client.post(f"/api/evidence/{json_upload['id']}/extract", headers=headers).json()
        assert json_result["status"] == "complete"
        json_claims = client.get(f"/api/evidence/{json_upload['id']}/extraction", headers=headers).json()["claims"]
        assert json_claims[0]["source_location"] == "$/project/claim"

        pdf = pymupdf.open()
        page = pdf.new_page()
        page.insert_text((72, 72), "The project claims 500 tCO2e removed in 2025.")
        pdf_bytes = pdf.tobytes()
        pdf.close()
        pdf_upload = client.post(
            f"/api/projects/{project['id']}/evidence", headers=headers,
            files={"file": ("report.pdf", pdf_bytes, "application/pdf")},
        ).json()
        pdf_result = client.post(f"/api/evidence/{pdf_upload['id']}/extract", headers=headers).json()
        assert pdf_result["page_count"] == 1
        pdf_claims = client.get(f"/api/evidence/{pdf_upload['id']}/extraction", headers=headers).json()["claims"]
        assert pdf_claims[0]["source_location"] == "page 1"

        bad_pdf = client.post(
            f"/api/projects/{project['id']}/evidence", headers=headers,
            files={"file": ("not-a-pdf.pdf", b"not a pdf", "application/pdf")},
        )
        assert bad_pdf.status_code == 422
        bad_mime = client.post(
            f"/api/projects/{project['id']}/evidence", headers=headers,
            files={"file": ("text.txt", b"plain text", "application/pdf")},
        )
        assert bad_mime.status_code == 415
        bad_json = client.post(
            f"/api/projects/{project['id']}/evidence", headers=headers,
            files={"file": ("invalid.json", b"{bad", "application/json")},
        )
        assert bad_json.status_code == 422
