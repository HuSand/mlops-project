# MLOps Project — Kelompok 7 (PSO B)

**Project**: Insurance Cross-Sell Prediction  
**Repository**: `HuSand/mlops-project`  
**Last updated**: 2026-06-18

**Anggota Tim:**
| Person | Nama | Pillar |
|---|---|---|
| P1 | Muhammad Daniel A. | CI Owner |
| P2 | Sandythia Lova R.K. | CD Owner |
| P3 | Gerald Marcell V.R. | CT Owner |
| P4 | Muhammad Ridho U. | CM Owner |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Tech Stack](#3-tech-stack)
4. [Repository Structure](#4-repository-structure)
5. [Branching Strategy](#5-branching-strategy)
6. [Team Task Division](#6-team-task-division)
7. [Pillar 1 — CI](#7-pillar-1--ci--continuous-integration)
8. [Pillar 2 — CT](#8-pillar-2--ct--continuous-training)
9. [Pillar 3a — CD Backend](#9-pillar-3a--cd-backend)
10. [Pillar 3b — CD Frontend](#10-pillar-3b--cd-frontend)
11. [Pillar 4 — CM](#11-pillar-4--cm--continuous-monitoring)
12. [Data Architecture](#12-data-architecture)
13. [Secrets dan IAM](#13-secrets-dan-iam)
14. [Onboarding Guide](#14-onboarding-guide)
15. [Runbook](#15-runbook)
16. [Glossary](#16-glossary)

---

## 1. Executive Summary

End-to-end MLOps pipeline untuk model prediksi cross-sell asuransi kendaraan, mengikuti standar Google MLOps Maturity Level 2. Pipeline mencakup full lifecycle: versioning data → training → deployment → monitoring, dengan retraining otomatis saat drift terdeteksi.

### Goals

- **Reproducibility**: setiap model traceable ke data, kode, dan config versinya.
- **Automation**: zero-touch deploy dari `git push` ke production.
- **Observability**: deteksi data drift harian, notifikasi Discord real-time.
- **Collaboration**: 4-person tim dengan ownership yang jelas.

### Key Metrics (Target)

| Metric | Target |
|---|---|
| CI pipeline duration | < 8 menit |
| Time from commit to production | < 25 menit |
| Test coverage | ≥ 70% |
| API response latency | < 200 ms |
| Drift detection cadence | Harian (23:00 UTC) |
| Model retrain cadence | Mingguan (Senin 02:00 UTC) + on drift |

---

## 2. Architecture Overview

### High-Level Flow

```
Developer commits
   │
   ├──► CI (ci.yml) ── lint + test + docker build
   │
   ├──► CD Frontend (cd-frontend.yml) ── Vercel deploy
   │
   └──► CD Backend (cd-backend.yml) ── Cloud Run deploy
              ▲
              │ trigger (setelah model baru di-promote)
              │
         CT Pipeline (ct-train.yml)
              ▲
              │ trigger (drift-retrain)
              │
         CM Monitor (monitor.yml) ── daily drift check
```

### Komponen Utama

| Layer | Komponen | Teknologi |
|---|---|---|
| **Source Control** | Repo, branch protection, Actions | GitHub |
| **CI/CD/CT/CM Orchestration** | 8 workflow files | GitHub Actions |
| **ML Training** | scikit-learn pipeline (DecisionTree/RF/GBM) | Python 3.11, MLflow |
| **Experiment Tracking** | Remote MLflow server di Cloud Run | MLflow 2.14.3 |
| **Data Versioning** | GCS remote | DVC 3.x |
| **Backend API** | FastAPI + Uvicorn, containerized | Docker (multi-stage) |
| **Backend Runtime** | Cloud Run (dev + prod) | GCP asia-southeast2 |
| **Frontend** | Next.js 14 (App Router) | Vercel |
| **Storage** | DVC data, MLflow artifacts, drift reports | Google Cloud Storage |
| **Analytics** | Prediction logs, drift metrics, API hits | BigQuery (`mlops` dataset) |
| **Monitoring** | Evidently AI 0.4.33, daily GitHub Action | monitor.yml |
| **Alerting** | Discord webhooks (CD, CT, CM, API hits) | 4 webhook channels |
| **Auth (GH → GCP)** | Keyless, tanpa SA JSON | Workload Identity Federation |

---

## 3. Tech Stack

### 3.1 Machine Learning

| Tool | Versi | Purpose |
|---|---|---|
| scikit-learn | 1.5.1 | Training (DecisionTree, RandomForest, GradientBoosting) |
| imbalanced-learn | 0.12.3 | SMOTE untuk class imbalance |
| MLflow | 2.14.3 | Experiment tracking + Model Registry (Staging/Production) |
| Pandera | ≥ 0.18.0 | DataFrame schema validation (`ml/validate.py`) |
| scipy | 1.11.3 | McNemar test untuk champion vs challenger |
| DVC | 3.67.1 | Data & model versioning, remote di GCS |
| PyYAML | 6.0.1 | Baca `config.yml` hyperparameter |

### 3.2 Backend Application

| Tool | Versi | Purpose |
|---|---|---|
| FastAPI | 0.111.1 | Web framework, async, auto OpenAPI docs |
| Uvicorn | 0.30.1 | ASGI server |
| Pydantic | 2.8.2 | Request/response schema validation |
| pandas | 2.2.2 | Preprocessing payload untuk inferensi |
| joblib | 1.4.2 | Deserialize `model.pkl` dari disk/GCS |
| google-cloud-storage | 3.12.0 | Download model dari GCS saat startup |
| google-cloud-bigquery | 3.25.0 | Log predictions + query analytics |

**Catatan**: Tidak ada database relasional (PostgreSQL/Redis). Semua persistence lewat BigQuery (analytics) dan GCS (model artifacts).

### 3.3 Frontend

| Tool | Purpose |
|---|---|
| Next.js 14 (App Router) | SSR/SSG, native Vercel integration |
| TypeScript | Type safety |
| TailwindCSS | Styling |
| Recharts | Charts di `/insights` dan `/monitoring` |

**Route yang aktif**: `/` (landing), `/predict` (form prediksi), `/insights` (business dashboard), `/monitoring` (CM dashboard)

### 3.4 Infrastructure

| Tool | Purpose |
|---|---|
| Docker (multi-stage) | Builder → runtime image, Python 3.10-slim |
| Google Artifact Registry | Container registry (`mlops-images`, region `asia-southeast2`) |
| Cloud Run | Serverless container runtime, backend dev + prod |
| Vercel | Frontend hosting, preview per PR |
| Workload Identity Federation | Keyless auth GitHub Actions → GCP (tanpa SA JSON key) |

### 3.5 Monitoring & Observability

| Tool | Purpose |
|---|---|
| Evidently AI 0.4.33 | Data drift detection (DataDriftPreset, threshold 0.3) |
| BigQuery | Analytics warehouse — `prediction_logs`, `drift_metrics`, `api_hits` |
| Discord webhooks | Alerting tim (4 channel) |
| GitHub Issues | Auto-created saat drift terdeteksi |
| GitHub Step Summary | CI/CT coverage + data summary |

### 3.6 Quality & Security

| Tool | Purpose |
|---|---|
| Ruff 0.6.2 | Python lint |
| pytest + pytest-cov | Testing, coverage gate ≥ 70% |
| Bandit | Python SAST (security static analysis) |
| ESLint | JS/TS lint |

---

## 4. Repository Structure

```
mlops-project/
├── .github/
│   └── workflows/
│       ├── ci.yml                  P1 — quality gate + docker validation
│       ├── cd-backend.yml          P2 — Cloud Run deploy
│       ├── cd-frontend.yml         P2 — Vercel deploy
│       ├── ct-train.yml            P3 — full CT pipeline
│       ├── monitor.yml             P4 — daily drift monitoring
│       ├── api-hit-digest.yml      P4 — 6-hourly API hit digest ke Discord
│       ├── data-validation.yml     P3 — standalone + dipanggil ct-train
│       ├── ab-test.yml             manual A/B test via Cloud Run traffic split
│       ├── seed-data.yml           seed data ke GCS
│       ├── seed-bigquery.yml       seed data ke BigQuery
│       └── docs.yml                mkdocs publish
│
├── app/                            FastAPI backend (SHARED — semua kontribusi)
│   ├── main.py                     FastAPI app + lifespan (model load)
│   ├── routes.py                   API routes: /predict, /api/v1/insights/*, /api/v1/monitoring/*
│   ├── model.py                    load model dari disk atau GCS
│   ├── bq_logger.py                log predictions + API hits ke BigQuery
│   ├── config.py                   env var config (APP_ENV, MODEL_VERSION, BQ_*)
│   └── schemas.py                  Pydantic InputData + PredictResponse
│
├── frontend/                       Next.js frontend (SHARED)
│   └── app/
│       ├── page.tsx                landing
│       ├── predict/                form prediksi
│       ├── insights/               business dashboard (Recharts, query /api/v1/insights/business)
│       └── monitoring/             CM dashboard (query /api/v1/monitoring/*)
│
├── ml/                             ML validation script
│   └── validate.py                 Pandera schema validation (dipanggil ct-train + data-validation)
│
├── steps/                          ML pipeline steps (dipanggil main.py)
│   ├── ingest.py
│   ├── clean.py
│   ├── train.py
│   └── predict.py
│
├── scripts/                        CT utility scripts
│   ├── promote_model.py            champion vs challenger (McNemar test)
│   ├── gen_model_card.py           generate model_card.md
│   ├── continuous_learning.py      merge BQ prediction data ke train.csv
│   └── evaluate.py
│
├── monitoring/                     CM scripts (dipanggil monitor.yml)
│   ├── evidently_report.py         run Evidently drift report
│   ├── fetch_production_data.py    query BQ prediction_logs
│   └── write_metrics_to_bq.py      write drift_metrics ke BQ
│
├── tests/                          pytest test suite
│   ├── test_app_api.py             FastAPI TestClient (mock model + BQ)
│   ├── test_bq_logger.py           unit test bq_logger
│   ├── test_clean.py               unit test steps/clean.py
│   ├── test_train.py               unit test steps/train.py
│   ├── test_validate.py            unit test ml/validate.py
│   ├── test_dataset.py
│   └── test_coverage_booster.py
│
├── data/                           DVC-tracked (train.csv, test.csv)
├── models/                         DVC-tracked (model.pkl)
├── main.py                         entry point training (train_with_mlflow())
├── config.yml                      hyperparameter (model name, params, paths)
├── dockerfile                      multi-stage: builder (python:3.10-slim) → runtime
├── dvc.yaml                        DVC pipeline stages
├── dvc.lock
├── pyproject.toml                  ruff config + pytest addopts (--cov ≥ 70%)
├── requirements.txt                full ML deps
├── requirements-serve.txt          runtime deps (fastapi, uvicorn, BQ client)
├── requirements-dev.txt            -r requirements.txt + ruff + pytest-cov + httpx
└── README.md
```

---

## 5. Branching Strategy

Model **2-branch deployment**: `dev` untuk staging, `prod` untuk production.

```
main ──── GitHub default branch (display + clone only)
           auto-synced dari prod post-merge

prod ──── production environment, branch protection ketat
 │         push → CD ke service "insurance-api" + Vercel prod
 │
 │   PR (promote)
 │
dev ──── staging environment, integration trunk
 │         push → CD ke service "insurance-api-dev" + Vercel preview
 │
 │   PR dari feat/*
 │
feat/* ── feature branches, bebas push
```

### Environment Mapping

| Branch | Cloud Run Service | Vercel |
|---|---|---|
| `dev` | `insurance-api-dev` (APP_ENV=dev) | Preview deployment |
| `prod` | `insurance-api` (APP_ENV=prod) | Production |
| PR to `dev` | build-check saja (docker build, no deploy) | Preview per PR |

---

## 6. Team Task Division

### Ownership

```
PERSONAL OWNERSHIP (pipeline)        SHARED OWNERSHIP (kode)

P1 → ci.yml                          app/        semua kontribusi
P2 → cd-backend.yml, cd-frontend     frontend/   semua kontribusi
P3 → ct-train.yml                    steps/      semua kontribusi
P4 → monitor.yml, api-hit-digest     tests/      semua kontribusi
```

### RACI Matrix

| Komponen | P1 (CI) | P2 (CD) | P3 (CT) | P4 (CM) |
|---|---|---|---|---|
| `ci.yml` | **R** | C | C | C |
| `cd-backend.yml` | C | **R** | I | C |
| `cd-frontend.yml` | C | **R** | I | I |
| `ct-train.yml` | C | I | **R** | C |
| `monitor.yml` | I | I | C | **R** |
| `api-hit-digest.yml` | I | I | I | **R** |
| GCS + IAM setup | I | C | C | **R** |
| GitHub Secrets | C | C | C | **R** |
| ML training code | shared | shared | shared | shared |
| Backend (app/) | shared | shared | shared | shared |
| Frontend | shared | shared | shared | shared |
| Tests | shared | shared | shared | shared |

**R** = Responsible · **C** = Consulted · **I** = Informed

---

## 7. Pillar 1 — CI : Continuous Integration

**File**: `.github/workflows/ci.yml`

### Trigger

- `push` ke branch `dev`, `main`
- `pull_request` ke branch `dev`, `main`

### Jobs

#### Job 1: `quality-gate` 🛡️

| Step | Tool | Detail |
|---|---|---|
| Setup Python 3.10 | `actions/setup-python@v5` | cache pip |
| Install deps | pip | `requirements-dev.txt` + `requirements-serve.txt` + `bandit` |
| Lint | Ruff 0.6.2 | `ruff check .` |
| Test + Coverage | pytest-cov | `pytest --cov-report=term-missing`, gate ≥ 70% (lihat `pyproject.toml`) |
| Coverage Summary | shell | ditulis ke `$GITHUB_STEP_SUMMARY` |
| Security Scan | Bandit | `bandit -r . -ll -ii -x ./venv,./tests` |

> **Kenapa install `requirements-serve.txt`?** Karena `app.routes` import `google.cloud.bigquery` yang ada di serve deps. Tanpanya, pytest gagal import error.

#### Job 2: `frontend-build` 🎨

| Step | Tool | Detail |
|---|---|---|
| Setup Node 20 | `actions/setup-node@v4` | cache npm, path `frontend/package-lock.json` |
| Install | npm | `npm ci` di folder `frontend/` |
| Lint | ESLint | `npm run lint` |
| Build | Next.js | `npm run build` (type-check + bundle) |

#### Job 3: `container-validation` 📦 *(needs: quality-gate)*

| Step | Tool | Detail |
|---|---|---|
| Docker build | Docker | `docker build -f dockerfile -t insurance-api-test .` |

### Coverage Config (`pyproject.toml`)

```toml
[tool.pytest.ini_options]
addopts = "--cov=steps --cov=ml --cov=app --cov-fail-under=70 -v"
testpaths = ["tests"]
```

---

## 8. Pillar 2 — CT : Continuous Training

**File**: `.github/workflows/ct-train.yml`

### Trigger

| Trigger | Kondisi |
|---|---|
| `schedule` | `0 2 * * 1` — Senin 02:00 UTC (09:00 WIB) |
| `push` | path `ml/**`, `config.yml`, `dvc.lock` |
| `workflow_dispatch` | manual via GitHub UI |
| `repository_dispatch` | event type `drift-retrain` (dari CM Monitor) |

### Jobs

```
auth → dvc-pull → data-validation → train → register → evaluate → promote* → artifact-versioning* → release* → notify
                                                                 ↘ KEEP_STAGING (notify only)
```
\* hanya jalan jika evaluasi menghasilkan keputusan `PROMOTE`

#### Job 1: auth
Authenticate ke GCP via Workload Identity Federation. Verifikasi akses ke `gs://dvc-mlops-ct-pipeline`.

#### Job 2: dvc-pull
Pull `data/train.csv` dan `data/test.csv` dari GCS remote DVC. Log row counts ke Step Summary.

#### Job 3: data-validation
Jalankan `python ml/validate.py data/train.csv` dan `data/test.csv --no-target` menggunakan Pandera. Jika gagal → auto-create GitHub Issue dengan label `data-quality`.

#### Job 4: train
1. **Continuous Learning**: `python scripts/continuous_learning.py` — merge data dari BigQuery `prediction_logs` ke `data/train.csv`, lalu `dvc push`.
2. Pastikan champion model ada di MLflow Production (auto-set jika belum ada).
3. Jalankan `python main.py` → `train_with_mlflow()`: training DecisionTree (atau model dari `config.yml`), log params/metrics ke MLflow, register model.

MLflow server: `https://mlflow-server-721834211942.asia-southeast1.run.app`

#### Job 5: register
`mlflow.create_model_version()` → stage ke **Staging** di Model Registry.

#### Job 6: evaluate (Champion vs Challenger)
Jalankan `python scripts/promote_model.py {run_id}`:
- Load champion dari `models:/insurance_model/Production`
- Load challenger dari `runs:/{run_id}/model`
- Hitung accuracy + ROC AUC keduanya di `data/test.csv`
- **McNemar test** untuk significance
- **Decision**: `PROMOTE` jika `accuracy_delta > 0.01` AND `p_value < 0.05`, else `KEEP_STAGING`
- Output: `promote_decision.json` (di-upload sebagai artifact)

Challenger & champion model juga di-copy ke `gs://mlflow-artifacts-mlops/models/history/`.

#### Job 7: promote *(jika PROMOTE)*
Transisi challenger dari Staging ke **Production** di MLflow Registry (`archive_existing_versions=True`). Generate `model_card.md` via `scripts/gen_model_card.py`.

#### Job 8: artifact-versioning *(jika PROMOTE)*
1. Jalankan ulang `main.py` untuk generate artifact terbaru
2. `dvc push` ke GCS
3. Copy `models/model.pkl` ke `gs://mlflow-artifacts-mlops/models/model.pkl`
4. Commit `dvc.lock` ke branch aktif dengan pesan `chore(model): retrain model-v{run_number}`

#### Job 9: release *(jika PROMOTE)*
Buat GitHub Release `model-v{run_number}` dengan `model_card.md` dan `promote_decision.json` sebagai assets.

#### Job 10: notify
Kirim Discord embed ke `DISCORD_WEBHOOK_CT` dengan decision, accuracy delta, dan p-value. Jika PROMOTE → trigger `gh workflow run cd-backend.yml`.

---

## 9. Pillar 3a — CD Backend

**File**: `.github/workflows/cd-backend.yml`

### Trigger

| Trigger | Behavior |
|---|---|
| `push` ke `dev` atau `prod` | auto-deploy (path filter: `app/**`, `dockerfile`, `requirements-serve.txt`) |
| `pull_request` ke `dev` atau `prod` | hanya `build-check` (docker build, tanpa deploy) |
| `workflow_dispatch` | manual deploy, opsional input `model_version` |

### Jobs

#### `build-check` *(PR only)*
`docker build -f dockerfile -t insurance-api-ci .` — validasi container bisa di-build.

#### `deploy` *(non-PR: push + workflow_dispatch)*

| Step | Detail |
|---|---|
| Resolve target | `dev` branch → service `insurance-api-dev`, APP_ENV=dev; `prod` branch → service `insurance-api`, APP_ENV=prod |
| Check GCP config | Guard: jika `GCP_PROJECT_ID` belum di-set, skip semua GCP steps (no fail) |
| Auth GCP | Workload Identity Federation |
| Configure Docker | `gcloud auth configure-docker asia-southeast2-docker.pkg.dev` |
| Build & Push | `docker build -f dockerfile -t {AR_IMAGE}:{sha} -t {AR_IMAGE}:latest .` dan push keduanya |
| Deploy Cloud Run | `gcloud run deploy {service} --image {AR_IMAGE}:{sha} --region asia-southeast2 --allow-unauthenticated --port 80 --service-account {RUNTIME_SA} --set-env-vars APP_ENV,MODEL_VERSION,GCS_MODEL_URI,ENABLE_BQ_LOGGING=true,BQ_PROJECT,BQ_DATASET=mlops,BQ_TABLE=prediction_logs` |
| Set Discord webhook | Update env var `DISCORD_WEBHOOK_API` = `DISCORD_WEBHOOK_DEPLOY` pada service |
| Smoke test | Curl `GET /` hingga 5x retry; 200 = sukses |
| Notify Discord | `if: always()` — embed warna hijau/merah dengan service URL dan run number |

**Artifact Registry**: `asia-southeast2-docker.pkg.dev/{GCP_PROJECT_ID}/mlops-images/insurance-api`

### Environment Variables di Cloud Run

| Env Var | Source | Purpose |
|---|---|---|
| `APP_ENV` | resolved dari branch | `dev` atau `prod` |
| `MODEL_VERSION` | `github.event.inputs.model_version` atau `github.run_number` | version tag |
| `GCS_MODEL_URI` | GitHub secret `GCS_MODEL_URI` | path model di GCS |
| `ENABLE_BQ_LOGGING` | hardcoded `true` | aktifkan log ke BigQuery |
| `BQ_PROJECT` | GitHub secret `GCP_PROJECT_ID` | GCP project |
| `BQ_DATASET` | hardcoded `mlops` | dataset BigQuery |
| `BQ_TABLE` | hardcoded `prediction_logs` | tabel log prediksi |
| `DISCORD_WEBHOOK_API` | secret `DISCORD_WEBHOOK_DEPLOY` | notifikasi per prediksi |
| `RUNTIME_SA` | secret | service account runtime Cloud Run |

---

## 10. Pillar 3b — CD Frontend

**File**: `.github/workflows/cd-frontend.yml`

### Trigger

`push` atau `pull_request` ke branch `dev`, path filter: `frontend/**`.

### Jobs

#### `deploy`

| Step | Detail |
|---|---|
| Setup Node 20 | |
| Install Vercel CLI | `npm install -g vercel@latest` |
| Resolve target | `push` → environment=production, flag `--prod`; `PR` → environment=preview |
| Pull Vercel settings | `vercel pull --yes --environment={env}` |
| Build | `vercel build [--prod]` |
| Deploy | `vercel deploy --prebuilt [--prod]` → capture URL |
| Smoke test | Curl URL hingga 5x retry; 2xx/3xx/401/403 = deployed |
| Notify Discord | `if: always()` — embed dengan URL Vercel dan environment |

**Secrets digunakan**: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `DISCORD_WEBHOOK_DEPLOY`

---

## 11. Pillar 4 — CM : Continuous Monitoring

### 11.1 Daily Drift Monitor

**File**: `.github/workflows/monitor.yml`  
**Trigger**: `schedule: 0 23 * * *` (23:00 UTC = 06:00 WIB) + `workflow_dispatch`

#### Jobs

```
fetch-data → drift-analysis ─┬─► storage-and-metrics
                              └─► alerting ──► (jika drift) create GH Issue + trigger CT
```

**Job 1: fetch-data**
- Auth ke GCP via WIF
- Query BigQuery `prediction_logs` untuk data produksi terbaru (`monitoring/fetch_production_data.py`)
- DVC pull `data/train.csv` sebagai reference data
- Upload `current_data.csv` + `reference_data.csv` sebagai artifact
- Output `SKIP=true` jika data tidak cukup (< 1 hari)

**Job 2: drift-analysis** *(skip jika SKIP=true)*
- Jalankan `monitoring/evidently_report.py` dengan Evidently 0.4.33
- Parse `drift_share` dari JSON output
- Threshold: `drift_share > 0.3` → `DRIFT_DETECTED=1`
- Output HTML report + metrics JSON sebagai artifact

**Job 3: storage-and-metrics** *(needs: drift-analysis)*
- Upload HTML report ke `gs://mlops-monitoring-reports/reports/drift_report_{date}.html`
- Tulis drift metrics ke BigQuery table `mlops.drift_metrics` (`monitoring/write_metrics_to_bq.py`)

**Job 4: alerting** *(needs: drift-analysis)*
- Jika `DRIFT_DETECTED=1`:
  - Buat GitHub Issue dengan label `drift-alert`, `priority-high`, link ke HTML report
  - `gh workflow run ct-train.yml --ref dev -f trigger=drift_alert`
- Discord notification ke `DISCORD_WEBHOOK_ALERT` (selalu, warna merah/hijau berdasarkan drift)

### 11.2 API Hit Digest

**File**: `.github/workflows/api-hit-digest.yml`  
**Trigger**: `schedule: 0 */6 * * *` (tiap 6 jam) + `workflow_dispatch`

Setiap prediksi yang masuk mencatat API hit ke BQ `mlops.api_hits`. Workflow ini:
1. Query BQ untuk aggregate hits 6 jam terakhir per endpoint
2. Jika total > 0: kirim Discord embed ke `DISCORD_WEBHOOK_DEPLOY`
3. Jika 0 hits: skip (tidak kirim)

> **Kenapa batch digest, bukan per-request?** Per-request Discord notification terlalu noisy. Setiap `/predict` juga tetap fire `notify_discord()` ke `DISCORD_WEBHOOK_PREDICT` (channel terpisah untuk prediksi individual).

### 11.3 A/B Test (Manual)

**File**: `.github/workflows/ab-test.yml`  
**Trigger**: `workflow_dispatch` — manual

Menggunakan Cloud Run **revision tags + traffic splitting** sebagai mekanisme A/B:

| Action | Behavior |
|---|---|
| `start` | Tag revision aktif sebagai `champion`, deploy challenger dengan tag `challenger`, split traffic N% ke challenger |
| `analyze` | Query BQ `prediction_logs` per model_version, bandingkan positive rate, kirim Discord verdict |
| `promote` | Pindahkan 100% traffic ke `challenger` tag |
| `rollback` | Pindahkan 100% traffic ke `champion` tag |

**Online analysis**: karena setiap Cloud Run revision log ke BQ dengan `MODEL_VERSION`-nya sendiri, perbandingan champion vs challenger dilakukan langsung dari `prediction_logs` — bukan offline batch.

---

## 12. Data Architecture

### 12.1 GCS Buckets

| Bucket | Isi | Digunakan oleh |
|---|---|---|
| `dvc-mlops-ct-pipeline` | `data/train.csv`, `data/test.csv` (DVC remote) | CT Pipeline, CM Monitor |
| `mlflow-artifacts-mlops` | MLflow experiment artifacts, `models/model.pkl` terbaru, history champion/challenger | CT Pipeline, CD Backend |
| `mlops-monitoring-reports` | HTML drift report harian | CM Monitor |

### 12.2 BigQuery Dataset: `mlops`

| Tabel | Schema (kolom utama) | Ditulis oleh | Dibaca oleh |
|---|---|---|---|
| `prediction_logs` | `input_payload` (JSON string), `timestamp`, `prediction` (int), `model_version` | `app/bq_logger.py` (per prediksi) | CM Monitor, api-hit-digest, routes `/api/v1/insights/*`, `/api/v1/monitoring/ops`, `/api/v1/ab/compare` |
| `drift_metrics` | `date`, `timestamp`, `dataset_drift`, `drift_share`, `number_of_columns`, `number_of_drifted_columns`, `drifted_features` (JSON), `missing_values_count`, `total_rows` | `monitoring/write_metrics_to_bq.py` | route `/api/v1/monitoring/latest` |
| `api_hits` | `endpoint`, `timestamp` | `app/bq_logger.py` (per API call) | `api-hit-digest.yml` |

### 12.3 Dual Payload Format (Gotcha!)

`prediction_logs.input_payload` punya **dua format berbeda**:
- **Production app**: field name `Gender`, `Age`, `HasDrivingLicense`, `RegionID`, `Switch`, `PastAccident`, `AnnualPremium`
- **Legacy seed (`auto-seed-v2`)**: field name `feature_0` s.d. `feature_6` (urutan sama)

Solusi di `app/routes.py`: fungsi `_norm_cte()` menggunakan `COALESCE(JSON_EXTRACT_SCALAR(input_payload, '$.Gender'), JSON_EXTRACT_SCALAR(input_payload, '$.feature_0'))` untuk semua query analytics — sehingga kedua format dihandle transparan.

### 12.4 Data Flow

```
User → POST /predict
         ├─► scikit-learn model.predict()
         ├─► bq_logger.log_prediction()  → BQ prediction_logs
         ├─► bq_logger.log_api_hit()     → BQ api_hits
         └─► bq_logger.notify_discord()  → Discord (DISCORD_WEBHOOK_PREDICT)

CT Pipeline → train.csv updated via CL
            → model.pkl → GCS (mlflow-artifacts-mlops)
            → MLflow Registry → Production stage

CM Monitor (daily) → fetch BQ prediction_logs
                   → fetch train.csv (DVC reference)
                   → Evidently drift analysis
                   → write BQ drift_metrics
                   → upload GCS drift_report.html
                   → (jika drift) trigger CT + GH Issue + Discord

CD Backend deploy → Cloud Run service
                 → pull model.pkl dari GCS_MODEL_URI saat startup
```

---

## 13. Secrets dan IAM

### 13.1 Workload Identity Federation (WIF)

Semua workflow GCP menggunakan **keyless auth** — tidak ada SA JSON key yang disimpan di GitHub.

```yaml
uses: google-github-actions/auth@v2
with:
  workload_identity_provider: 'projects/721834211942/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
  service_account: 'mlops-ct-pipeline@project-d50e88c7-b681-48d4-b1b.iam.gserviceaccount.com'
```

**GCP Project ID**: `project-d50e88c7-b681-48d4-b1b`  
**GCP Project Number**: `721834211942`  
**Deploy Region**: `asia-southeast2` (Jakarta)

### 13.2 GitHub Secrets

| Secret | Digunakan oleh | Isi |
|---|---|---|
| `GCP_PROJECT_ID` | cd-backend, ct-train, monitor, ab-test | GCP project ID |
| `GCS_MODEL_URI` | cd-backend | `gs://mlflow-artifacts-mlops/models/model.pkl` |
| `RUNTIME_SA` | cd-backend, ab-test | email SA untuk runtime Cloud Run |
| `VERCEL_TOKEN` | cd-frontend | Vercel auth token |
| `VERCEL_ORG_ID` | cd-frontend | Vercel org ID |
| `VERCEL_PROJECT_ID` | cd-frontend | Vercel project ID |
| `MLFLOW_TRACKING_URI` | ct-train | URL MLflow server |
| `DISCORD_WEBHOOK_DEPLOY` | cd-backend, cd-frontend, api-hit-digest, ab-test | CD + API digest channel |
| `DISCORD_WEBHOOK_CT` | ct-train | CT pipeline result channel |
| `DISCORD_WEBHOOK_ALERT` | monitor | Drift alert channel |
| `DISCORD_WEBHOOK_PREDICT` | Cloud Run env var via cd-backend | Per-prediction notification |

### 13.3 IAM — Service Account CT Pipeline

**SA**: `mlops-ct-pipeline@project-d50e88c7-b681-48d4-b1b.iam.gserviceaccount.com`

Roles yang dibutuhkan untuk **GitHub Actions** (via WIF):
- `roles/storage.admin` — DVC push/pull ke GCS
- `roles/run.admin` — deploy Cloud Run
- `roles/artifactregistry.writer` — push Docker image ke AR
- `roles/bigquery.jobUser` + `roles/bigquery.dataViewer` — query BQ di CI/monitor
- `roles/iam.serviceAccountUser` — untuk set `--service-account` di Cloud Run deploy

### 13.4 IAM — Cloud Run Runtime SA (`RUNTIME_SA`)

Roles yang dibutuhkan agar backend bisa **query BigQuery saat serving**:
- `roles/bigquery.jobUser` — submit query jobs
- `roles/bigquery.dataViewer` — baca data dari dataset `mlops`
- `roles/storage.objectViewer` — download model dari GCS bucket

> **Gotcha penting**: `bq query` dari gcloud CLI berhasil ≠ Python `google.cloud.bigquery.Client()` punya akses. Python client pakai ADC/SA yang berbeda. Kalau endpoint `/api/v1/insights/*` return 403/500, cek IAM Cloud Run runtime SA.

---

## 14. Onboarding Guide

### Setup Lokal

```bash
# 1. Clone
git clone https://github.com/HuSand/mlops-project.git
cd mlops-project

# 2. Python environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt -r requirements-serve.txt

# 3. Frontend
cd frontend && npm ci && cd ..

# 4. Tools
pip install "dvc[gs]"
# gcloud CLI: https://cloud.google.com/sdk/docs/install

# 5. Auth GCP
gcloud auth login
gcloud auth application-default login
gcloud config set project project-d50e88c7-b681-48d4-b1b

# 6. Pull data
dvc pull

# 7. Training lokal
python main.py  # butuh MLFLOW_TRACKING_URI di-set, atau gunakan local mode

# 8. Jalankan API lokal
MODEL_PATH=models/model.pkl uvicorn app.main:app --reload --port 8000

# 9. Jalankan frontend lokal
cd frontend && npm run dev
```

### Verifikasi Akses

| Check | Command |
|---|---|
| GCS bucket data | `gsutil ls gs://dvc-mlops-ct-pipeline` |
| GCS bucket artifacts | `gsutil ls gs://mlflow-artifacts-mlops` |
| Cloud Run services | `gcloud run services list --region asia-southeast2` |
| BigQuery dataset | `bq ls project-d50e88c7-b681-48d4-b1b:mlops` |
| MLflow UI | buka `https://mlflow-server-721834211942.asia-southeast1.run.app` |

### Run Tests

```bash
pytest --cov=steps --cov=ml --cov=app -v
```

---

## 15. Runbook

### Incident: Backend 5xx / Model Not Loaded

**Symptom**: `GET /` return `model_loaded: false`, `POST /predict` return 503.

```bash
# Cek logs Cloud Run
gcloud run services logs read insurance-api-dev --region asia-southeast2 --limit 50

# Cek env vars
gcloud run services describe insurance-api-dev --region asia-southeast2 --format='value(spec.template.spec.containers[0].env)'

# Pastikan GCS_MODEL_URI benar dan model ada
gsutil ls gs://mlflow-artifacts-mlops/models/model.pkl
```

**Penyebab umum**: `GCS_MODEL_URI` salah atau model.pkl belum di-push ke GCS setelah training.

---

### Incident: Analytics Endpoint 403/500

**Symptom**: `/api/v1/insights/business` atau `/api/v1/monitoring/latest` return error.

**Cek**:
1. Pastikan `ENABLE_BQ_LOGGING=true` dan `BQ_PROJECT` ter-set di Cloud Run env vars
2. Pastikan runtime SA punya `roles/bigquery.jobUser` + `roles/bigquery.dataViewer`
3. Lihat Cloud Run logs untuk pesan error BigQuery spesifik

```bash
# Cek IAM runtime SA
gcloud projects get-iam-policy project-d50e88c7-b681-48d4-b1b \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:{RUNTIME_SA_EMAIL}"
```

---

### Incident: Drift Terdeteksi (Otomatis Ditangani)

**Flow otomatis**:
1. `monitor.yml` buat GitHub Issue dengan label `drift-alert`
2. Auto-trigger `ct-train.yml` dengan input `trigger=drift_alert`
3. CT Pipeline train ulang, evaluate champion vs challenger
4. Jika PROMOTE → model baru di-deploy via `cd-backend.yml`

**Verifikasi manual**:
1. Buka GitHub Issue yang dibuat, cek link ke HTML report
2. Cek tab Actions untuk run `ct-train.yml`
3. Setelah CT selesai, cek MLflow Registry untuk versi model baru

---

### Rollback

| Apa | Command |
|---|---|
| Backend ke revision sebelumnya | `gcloud run services update-traffic insurance-api-dev --to-revisions={prev-revision}=100 --region asia-southeast2` |
| A/B test ke champion | `gh workflow run ab-test.yml -f action=rollback` |
| Model di MLflow | Promote versi sebelumnya ke Production via MLflow UI |

---

## 16. Glossary

| Term | Arti |
|---|---|
| **CI** | Continuous Integration — validasi setiap kode sebelum merge |
| **CT** | Continuous Training — retrain model otomatis |
| **CD** | Continuous Deployment — deploy otomatis ke staging/prod |
| **CM** | Continuous Monitoring — deteksi data drift dan degradasi model |
| **WIF** | Workload Identity Federation — keyless auth dari GitHub ke GCP |
| **DVC** | Data Version Control — versioning file besar (data, model) |
| **GCS** | Google Cloud Storage — object storage di GCP |
| **AR** | Artifact Registry — registry Docker image di GCP |
| **MLflow Registry** | Model store dengan stages: None → Staging → Production → Archived |
| **Champion** | Model yang sedang aktif di Production |
| **Challenger** | Model baru dari training terbaru, di Staging |
| **McNemar test** | Statistical test untuk membandingkan dua classifier berpasangan |
| **SMOTE** | Synthetic Minority Over-sampling Technique — handle class imbalance |
| **Pandera** | Library validasi DataFrame schema untuk Python |
| **Evidently** | Library open-source untuk data/model drift detection |
| **Cloud Run** | GCP serverless container platform (scale to zero) |
| **revision tag** | Label pada Cloud Run revision untuk routing traffic (dipakai A/B test) |
| **drift_share** | Fraksi fitur yang mengalami drift (Evidently output); threshold 0.3 |
| **BQ** | BigQuery — serverless analytics warehouse GCP |
| **RACI** | Responsible, Accountable, Consulted, Informed — responsibility matrix |

---

*Untuk pertanyaan atau update, buka PR ke branch `dev` dan tag owner pillar yang relevan.*
