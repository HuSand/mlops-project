"""Tests untuk best-effort logging & notifikasi Discord di app.bq_logger."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import bq_logger, config  # noqa: E402


def test_log_api_hit_noop_when_disabled(monkeypatch):
    """Saat ENABLE_BQ_LOGGING false, klien BQ tidak pernah dibuat."""
    monkeypatch.setattr(config, "ENABLE_BQ_LOGGING", False)

    def fail():
        raise AssertionError("_get_client should not be called when disabled")

    monkeypatch.setattr(bq_logger, "_get_client", fail)
    bq_logger.log_api_hit("/api/v1/monitoring/latest")  # tidak melempar


def test_log_api_hit_inserts_when_enabled(monkeypatch):
    """Saat enabled, insert satu baris {endpoint, timestamp} ke tabel api_hits."""
    monkeypatch.setattr(config, "ENABLE_BQ_LOGGING", True)
    captured = {}

    class FakeClient:
        def insert_rows_json(self, table_id, rows):
            captured["table_id"] = table_id
            captured["rows"] = rows
            return []

    monkeypatch.setattr(bq_logger, "_get_client", lambda: FakeClient())
    bq_logger.log_api_hit("/api/v1/monitoring/ops")

    assert captured["table_id"].endswith("api_hits")
    assert captured["rows"][0]["endpoint"] == "/api/v1/monitoring/ops"
    assert "timestamp" in captured["rows"][0]


def test_log_api_hit_never_raises(monkeypatch):
    """Kegagalan BQ tidak boleh memecah request utama."""
    monkeypatch.setattr(config, "ENABLE_BQ_LOGGING", True)

    def boom():
        raise RuntimeError("bq down")

    monkeypatch.setattr(bq_logger, "_get_client", boom)
    bq_logger.log_api_hit("/x")  # tidak melempar


def test_log_prediction_disabled(monkeypatch):
    """Saat ENABLE_BQ_LOGGING false, klien BQ tidak pernah dibuat."""
    monkeypatch.setattr(config, "ENABLE_BQ_LOGGING", False)

    def fail():
        raise AssertionError("_get_client should not be called when disabled")

    monkeypatch.setattr(bq_logger, "_get_client", fail)
    bq_logger.log_prediction({"a": 1}, 0)  # tidak melempar


def test_notify_discord_builds_embed(monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_PREDICT", "https://example.com/hook")
    captured = {}
    monkeypatch.setattr(
        bq_logger.requests,
        "post",
        lambda url, json=None, timeout=None: captured.update(url=url, json=json),
    )
    bq_logger.notify_discord({"Gender": "Male", "Age": 30}, 1)

    assert captured["url"] == "https://example.com/hook"
    assert "Prediksi Baru" in captured["json"]["embeds"][0]["title"]


def test_notify_discord_noop_without_env(monkeypatch):
    monkeypatch.delenv("DISCORD_WEBHOOK_PREDICT", raising=False)
    calls = {"n": 0}
    monkeypatch.setattr(
        bq_logger.requests, "post", lambda *a, **k: calls.__setitem__("n", calls["n"] + 1)
    )
    bq_logger.notify_discord({"Gender": "Male"}, 0)
    assert calls["n"] == 0
