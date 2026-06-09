"""Tests untuk best-effort logging & notifikasi Discord di app.bq_logger."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import bq_logger, config  # noqa: E402


def test_notify_api_hit_noop_without_env(monkeypatch):
    """Tanpa DISCORD_WEBHOOK_API, tidak ada request yang dikirim."""
    monkeypatch.delenv("DISCORD_WEBHOOK_API", raising=False)
    calls = {"n": 0}
    monkeypatch.setattr(
        bq_logger.requests, "post", lambda *a, **k: calls.__setitem__("n", calls["n"] + 1)
    )
    bq_logger.notify_api_hit("/api/v1/monitoring/latest", {"drift_detected": True})
    assert calls["n"] == 0


def test_notify_api_hit_posts_with_env(monkeypatch):
    """Dengan env terisi, POST ke webhook yang benar + embed berisi endpoint."""
    monkeypatch.setenv("DISCORD_WEBHOOK_API", "https://example.com/hook")
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json

    monkeypatch.setattr(bq_logger.requests, "post", fake_post)
    bq_logger.notify_api_hit("/api/v1/monitoring/latest", {"drift_detected": True})

    assert captured["url"] == "https://example.com/hook"
    fields = captured["json"]["embeds"][0]["fields"]
    assert fields[0]["value"] == "/api/v1/monitoring/latest"
    assert any(f["name"] == "drift_detected" for f in fields)


def test_notify_api_hit_never_raises(monkeypatch):
    """Kegagalan jaringan tidak boleh memecah request utama."""
    monkeypatch.setenv("DISCORD_WEBHOOK_API", "https://example.com/hook")

    def boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(bq_logger.requests, "post", boom)
    # Tidak melempar exception
    bq_logger.notify_api_hit("/x")


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
