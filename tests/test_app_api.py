"""Tests integrasi untuk FastAPI app (health, predict, monitoring) memakai
TestClient. Semua dependency eksternal (model, BigQuery, Discord) di-mock —
tidak ada panggilan jaringan nyata.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app  # noqa: E402
from app import model as model_mod  # noqa: E402
from app import routes  # noqa: E402

VALID_PAYLOAD = {
    "Gender": "Male",
    "Age": 30,
    "HasDrivingLicense": 1,
    "RegionID": 5,
    "Switch": 0,
    "PastAccident": "No",
    "AnnualPremium": 1000.0,
}


@pytest.fixture
def client():
    # Tanpa context manager => lifespan tidak memuat model nyata; state default None.
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_model():
    model_mod.state["model"] = None
    yield
    model_mod.state["model"] = None


class _FakeModel:
    def predict(self, df):
        return [1]


# ----------------------------- health -----------------------------
def test_health(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["health_check"] == "OK"
    assert body["model_loaded"] is False


# ----------------------------- predict -----------------------------
def test_predict_without_model_returns_503(client):
    r = client.post("/predict", json=VALID_PAYLOAD)
    assert r.status_code == 503


def test_predict_ok(client, monkeypatch):
    model_mod.state["model"] = _FakeModel()
    monkeypatch.setattr(routes.bq_logger, "log_prediction", lambda *a, **k: None)
    monkeypatch.setattr(routes.bq_logger, "notify_discord", lambda *a, **k: None)

    r = client.post("/predict", json=VALID_PAYLOAD)
    assert r.status_code == 200
    body = r.json()
    assert body["predicted_class"] == 1
    assert "model_version" in body


# --------------------------- monitoring ---------------------------
class _FakeRow:
    date = "2026-06-09"
    timestamp = datetime(2026, 6, 9, 12, 0, tzinfo=timezone.utc)
    dataset_drift = True
    drift_share = 0.5
    number_of_columns = 7
    number_of_drifted_columns = 3
    drifted_features = '["feature_1", "feature_3"]'
    missing_values_count = 0
    total_rows = 500


class _FakeQueryJob:
    def __init__(self, rows):
        self._rows = rows

    def result(self):
        return self._rows


class _FakeBQClient:
    def __init__(self, rows):
        self._rows = rows

    def query(self, _q):
        return _FakeQueryJob(self._rows)


def _patch_bq(monkeypatch, rows):
    monkeypatch.setattr(routes.bigquery, "Client", lambda *a, **k: _FakeBQClient(rows))
    monkeypatch.setattr(routes.bq_logger, "log_api_hit", lambda *a, **k: None)


def test_monitoring_latest_success(client, monkeypatch):
    _patch_bq(monkeypatch, [_FakeRow()])
    r = client.get("/api/v1/monitoring/latest")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert body["data"]["summary"]["drift_detected"] is True
    assert body["data"]["summary"]["drifted_columns_count"] == 3
    assert body["data"]["drift_details"] == ["feature_1", "feature_3"]
    assert body["data"]["data_health"]["total_predictions"] == 500


def test_monitoring_latest_empty(client, monkeypatch):
    _patch_bq(monkeypatch, [])
    r = client.get("/api/v1/monitoring/latest")
    assert r.status_code == 200
    assert r.json()["status"] == "error"


# ------------------------ analytics endpoints ------------------------
class _RoutingJob:
    def __init__(self, rows):
        self._rows = rows

    def result(self):
        return self._rows


class _RoutingBQClient:
    """Returns fake rows based on a distinctive substring of each query SQL."""

    def __init__(self, routes):
        self._routes = routes

    def query(self, sql):
        for substr, rows in self._routes:
            if substr in sql:
                return _RoutingJob(rows)
        raise AssertionError(f"Unexpected query: {sql[:120]}")


def test_business_insights_success(client, monkeypatch):
    from datetime import date

    route_table = [
        ("total_scored", [{
            "total_scored": 3000, "interest_rate": 50.7, "avg_premium": 23182.0,
            "interested_leads": 1521, "avg_premium_interested": 23669.0,
        }]),
        ("AS gender, COUNT(*) AS n", [
            {"gender": "Female", "n": 1496, "interest_pct": 51.5, "avg_premium": 23369.0},
            {"gender": "Male", "n": 1504, "interest_pct": 49.9, "avg_premium": 22995.0},
        ]),
        ("WHEN age < 30", [
            {"band": "<30", "n": 582, "interest_pct": 47.4},
            {"band": "30-44", "n": 876, "interest_pct": 52.6},
        ]),
        ("WHEN premium < 5000", [
            {"band": "<5k", "n": 822, "interest_pct": 48.9},
            {"band": "30k+", "n": 1095, "interest_pct": 51.3},
        ]),
        ("AS value, COUNT(*) AS n", [
            {"value": "No", "n": 1306, "interest_pct": 52.7},
            {"value": "Yes", "n": 1369, "interest_pct": 49.1},
        ]),
        # Query is ORDER BY date DESC; endpoint reverses to chronological.
        ("AS interested", [
            {"date": date(2026, 6, 9), "total": 120, "interested": 70, "interest_pct": 58.3},
            {"date": date(2026, 6, 8), "total": 100, "interested": 50, "interest_pct": 50.0},
        ]),
    ]
    monkeypatch.setattr(routes.bigquery, "Client", lambda *a, **k: _RoutingBQClient(route_table))

    r = client.get("/api/v1/insights/business")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["kpis"]["total_scored"] == 3000
    assert data["kpis"]["interested_leads"] == 1521
    assert len(data["by_gender"]) == 2
    assert data["by_age_band"][0]["band"] == "<30"
    assert data["by_premium_band"][0]["band"] == "<5k"
    assert len(data["by_past_accident"]) == 2
    # trend reversed to chronological; newest is last; dates serialized to str
    assert data["trend"][-1]["date"] == "2026-06-09"
    assert isinstance(data["trend"][-1]["date"], str)


def test_monitoring_ops_success(client, monkeypatch):
    from datetime import date, datetime, timezone

    route_table = [
        ("total_predictions", [{
            "total_predictions": 3000,
            "last_prediction_ts": datetime(2026, 6, 9, 4, 31, tzinfo=timezone.utc),
        }]),
        # ORDER BY date DESC; endpoint reverses to chronological.
        ("AS date, COUNT(*) AS n", [
            {"date": date(2026, 6, 9), "n": 2000},
            {"date": date(2026, 6, 8), "n": 1000},
        ]),
        ("model_version, COUNT(*) AS n", [
            {"model_version": "auto-seed-v2", "n": 2000},
            {"model_version": "auto-seed", "n": 1000},
        ]),
    ]
    monkeypatch.setattr(routes.bigquery, "Client", lambda *a, **k: _RoutingBQClient(route_table))

    r = client.get("/api/v1/monitoring/ops")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_predictions"] == 3000
    assert data["last_prediction_ts"].startswith("2026-06-09")
    assert data["volume_by_day"][-1]["n"] == 2000
    assert data["by_model_version"][0]["model_version"] == "auto-seed-v2"


def test_ab_compare_success(client, monkeypatch):
    from datetime import datetime, timezone

    rows = [
        {"model_version": "auto-seed-v2", "n": 2000, "positive_rate": 51.4,
         "first_seen": datetime(2026, 6, 7, tzinfo=timezone.utc),
         "last_seen": datetime(2026, 6, 9, 4, tzinfo=timezone.utc)},
        {"model_version": "challenger-30", "n": 100, "positive_rate": 33.3,
         "first_seen": datetime(2026, 6, 9, 9, tzinfo=timezone.utc),
         "last_seen": datetime(2026, 6, 9, 10, tzinfo=timezone.utc)},
    ]
    monkeypatch.setattr(
        routes.bigquery, "Client",
        lambda *a, **k: _RoutingBQClient([("AS positive_rate", rows)]),
    )

    r = client.get("/api/v1/ab/compare?hours=168")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_predictions"] == 2100
    assert data["versions"][0]["model_version"] == "auto-seed-v2"
    assert data["versions"][0]["traffic_pct"] == round(2000 / 2100 * 100, 1)
    assert data["comparison"]["champion"] == "auto-seed-v2"
    assert data["comparison"]["challenger"] == "challenger-30"
    assert data["comparison"]["positive_rate_delta"] == -18.1


# ----------------------------- lifespan -----------------------------
def test_lifespan_loads_model(monkeypatch):
    monkeypatch.setattr(model_mod, "load_model", lambda: _FakeModel())
    with TestClient(app) as c:
        assert c.get("/").json()["model_loaded"] is True


def test_lifespan_handles_model_failure(monkeypatch):
    def boom():
        raise RuntimeError("no model available")

    monkeypatch.setattr(model_mod, "load_model", boom)
    with TestClient(app) as c:
        assert c.get("/").json()["model_loaded"] is False


# ----------------------------- model utils -----------------------------
def test_download_from_gcs_invalid_uri():
    with pytest.raises(ValueError):
        model_mod.download_from_gcs("http://not-gcs", Path("ignored.pkl"))


def test_load_model_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(model_mod.config, "MODEL_PATH", tmp_path / "none.pkl")
    monkeypatch.setattr(model_mod.config, "GCS_MODEL_URI", None)
    with pytest.raises(FileNotFoundError):
        model_mod.load_model()


def test_get_model_returns_state():
    sentinel = object()
    model_mod.state["model"] = sentinel
    assert model_mod.get_model() is sentinel
