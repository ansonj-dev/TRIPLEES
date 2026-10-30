from __future__ import annotations

import os
import subprocess
import sys

import pytest

from services.api.app import storage


def test_s3_compatible_storage_round_trip_uses_configured_bucket_and_prefix(monkeypatch):
    objects = {}

    class Body:
        def __init__(self, value):
            self.value = value

        def read(self):
            return self.value

    class FakeS3:
        def put_object(self, **kwargs):
            objects[(kwargs["Bucket"], kwargs["Key"])] = kwargs

        def get_object(self, **kwargs):
            return {"Body": Body(objects[(kwargs["Bucket"], kwargs["Key"])]["Body"])}

    monkeypatch.setattr(storage, "OBJECT_STORAGE_BUCKET", "phase8-test-bucket")
    monkeypatch.setattr(storage, "OBJECT_STORAGE_PREFIX", "triplees/evidence")
    monkeypatch.setattr(storage, "_s3_client", lambda: FakeS3())

    storage.put_evidence("upload-123.txt", b"evidence bytes", "text/plain")

    assert storage.get_evidence("upload-123.txt") == b"evidence bytes"
    saved = objects[("phase8-test-bucket", "triplees/evidence/upload-123.txt")]
    assert saved["ContentType"] == "text/plain"


def test_storage_rejects_path_traversal():
    with pytest.raises(storage.EvidenceStorageError):
        storage.get_evidence("../outside.txt")


def test_production_api_refuses_prototype_authentication():
    env = os.environ.copy()
    env.update({
        "APP_ENV": "production",
        "DATABASE_URL": "postgresql://triplees:secret@localhost/triplees",
        "OBJECT_STORAGE_BUCKET": "triplees-test",
        "CORS_ORIGINS": "https://app.example.test",
        "VERICARB_TOKEN_SECRET": "a" * 48,
        "AUTO_MIGRATE": "false",
        "SEED_DEMO_DATA": "false",
    })
    result = subprocess.run(
        [sys.executable, "-c", "import services.api.app.main"],
        capture_output=True, text=True, env=env, check=False,
    )

    assert result.returncode != 0
    assert "Production API startup is blocked" in result.stderr
