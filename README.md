# MLOps Pipeline Documentation

**Project**: Insurance Cross-Sell Prediction
**Repository**: `mlops-project`
**Document version**: 1.0
**Last updated**: 2026-05-25
**Maintained by**: MLOps Team (4 members)

---
# MLOps Project - Kelompok 7 (PSO B)

**Anggota Tim:**
- P1: Muhammad Daniel A. (CI Owner)
- P2: Sandythia Lova R.K. (CT Owner)
- P3: Gerald Marcell V.R. (CD Owner)
- P4: Muhammad Ridho U. (CM Owner)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Tech Stack and Justification](#3-tech-stack-and-justification)
4. [Repository Structure](#4-repository-structure)
5. [Branching Strategy and Environments](#5-branching-strategy-and-environments)
6. [Team Task Division](#6-team-task-division)
7. [Pillar 1 — CI : Continuous Integration](#7-pillar-1--ci--continuous-integration)
8. [Pillar 2 — CT : Continuous Training](#8-pillar-2--ct--continuous-training)
9. [Pillar 3a — CD Backend](#9-pillar-3a--cd-backend)
10. [Pillar 3b — CD Frontend](#10-pillar-3b--cd-frontend)
11. [Pillar 4 — CM : Continuous Monitoring](#11-pillar-4--cm--continuous-monitoring)
12. [Data Architecture](#12-data-architecture)
13. [Secrets and IAM Management](#13-secrets-and-iam-management)
14. [Onboarding Guide](#14-onboarding-guide)
15. [Runbook and Incident Response](#15-runbook-and-incident-response)
16. [Glossary](#16-glossary)

---

## 1. Executive Summary

This project implements an end-to-end MLOps pipeline for an insurance cross-sell prediction model, following Google MLOps Maturity Level 2 standards. The system covers the full lifecycle from data versioning to model deployment and continuous monitoring, with automated retraining triggered by data drift detection.

### Goals

- **Reproducibility**: every model is traceable to its data, code, and config version.
- **Automation**: zero-touch deploy from `git push` to production.
- **Observability**: detect data drift and model degradation early.
- **Collaboration**: 4-person team with clear ownership and shared application code.

### Key Metrics (Target)

| Metric | Target |
|---|---|
| CI pipeline duration | under 8 minutes |
| Time from commit to production | under 25 minutes |
| Test coverage | at least 70 percent |
| API response p95 latency | under 200 ms |
| Drift detection cadence | daily at 06:00 WIB |
| Model retrain cadence | weekly + on drift event |

---

## 2. Architecture Overview

The architecture is organized into **three swimlanes** (Developers / GitHub / Cloud) and **five pillars** (CI / CT / CD-BE / CD-FE / CM).

### High-Level Flow

```
Developer commits → GitHub triggers workflow → Cloud deploys → Runtime serves users → Monitoring detects drift → Loop back to CT
```

### Layered Architecture

| Layer | Purpose | Key Components |
|---|---|---|
| **Developer Layer** | Local development environment | VS Code, Git, Python 3.10, Node.js 20, Docker, DVC, gcloud, Vercel CLI |
| **Source and Orchestration** | Version control and pipeline trigger | GitHub repo, branch protection, GitHub Actions, GitHub Environments |
| **Pipeline Layer** | Automation workflows | 6 workflow files (ci, ct-train, db-migrate, cd-backend, cd-frontend, monitor) |
| **Storage Layer** | Persistent data and artifacts | GCS bucket (data, model, reports, backup), GHCR (Docker images), MLflow tracking server |
| **Database Layer** | Application and analytics data | Cloud SQL PostgreSQL 16, Memorystore Redis 7, BigQuery warehouse |
| **Runtime Layer** | Live application | Cloud Run (FastAPI backend dev/prod), Vercel (Next.js frontend dev/prod) |
| **Observability Layer** | Monitoring and alerting | Evidently AI, Sentry, Cloud Logging, Cloud Monitoring, Looker Studio, Discord webhook |

See `docs/diagrams/` for visual representations.

---

## 3. Tech Stack and Justification

### 3.1 Source Control and Orchestration

| Tool | Purpose | Why chosen |
|---|---|---|
| **Git + GitHub** | Version control, code review, project board | Industry standard, integrated with Actions and Environments |
| **GitHub Actions** | CI/CD/CT/CM orchestrator | Native to GitHub, free for public/student tier, YAML simple, marketplace rich |
| **GitHub Environments** | Approval gate, environment-scoped secrets | Built-in production gating, no external tool needed |

### 3.2 Machine Learning

| Tool | Purpose | Why chosen |
|---|---|---|
| **scikit-learn 1.5.1** | Model training (DecisionTree, RandomForest, GradientBoosting) | Standard for classical ML, well-supported, fast for small dataset |
| **imbalanced-learn (SMOTE)** | Handle class imbalance | Required because target distribution is skewed |
| **MLflow 2.14.3** | Experiment tracking and Model Registry | Open-source, supports all major ML frameworks, has Registry stages |
| **Pandera** | DataFrame schema validation | Decorator-based, integrates with pytest, prevents data quality regression |

### 3.3 Data Versioning

| Tool | Purpose | Why chosen |
|---|---|---|
| **DVC 3.51** | Data and model versioning | Git-compatible, supports GCS remote, reproducible pipelines via `dvc.yaml` |
| **GCS (Google Cloud Storage)** | Remote artifact storage | Cheap, scalable, integrates with DVC and MLflow |

### 3.4 Application Stack

#### Backend (FastAPI)

| Tool | Purpose | Why chosen |
|---|---|---|
| **FastAPI 0.111** | Web framework | Async, type-safe via Pydantic, auto OpenAPI docs |
| **Uvicorn** | ASGI server | High performance, production-ready |
| **SQLAlchemy 2.0** | ORM | Mature, async support, schema migrations via Alembic |
| **asyncpg** | PostgreSQL async driver | Fastest Python Postgres driver |
| **redis-py** | Redis client | Caching, rate limiting, JWT blacklist |
| **Alembic** | DB schema migration | Standard SQLAlchemy migration tool |
| **joblib** | Model serialization | Native to scikit-learn |

#### Frontend (Next.js)

| Tool | Purpose | Why chosen |
|---|---|---|
| **Next.js 14 (App Router)** | React framework | SSR/SSG, edge functions, native Vercel integration |
| **TypeScript** | Type safety | Catch errors before runtime |
| **TailwindCSS** | Styling | Utility-first, small bundle |
| **shadcn/ui** | Component library | Accessible, customizable, no runtime overhead |
| **TanStack Query** | Data fetching and caching | Smart cache, optimistic updates |
| **Playwright** | E2E testing | Cross-browser, reliable |

### 3.5 Containerization and Deployment

| Tool | Purpose | Why chosen |
|---|---|---|
| **Docker (multi-stage)** | Container image build | Smaller production image, security isolation |
| **GHCR** | Container registry | Free with GitHub, integrated authentication |
| **Cosign** | Image signing | Supply chain security (keyless OIDC) |
| **Cloud Run** | Backend serverless runtime | Scale-to-zero, GCP-native, Docker-based |
| **Vercel** | Frontend hosting | Best DX for Next.js, global CDN, preview per PR |
| **Cloud SQL Proxy** | Secure DB connection | No public IP needed, IAM-based auth |

### 3.6 Database Layer

| Tool | Purpose | Why chosen |
|---|---|---|
| **Cloud SQL PostgreSQL 16** | Primary DB (app + MLflow backend) | ACID, strong type system, JSON support, MLflow native support |
| **Memorystore Redis 7** | Cache, rate limiting, sessions | In-memory speed, scales independently of Cloud Run |
| **BigQuery** | Analytics warehouse | Scale to petabytes, native Looker Studio support, free tier generous |

### 3.7 Monitoring and Observability

| Tool | Purpose | Why chosen |
|---|---|---|
| **Evidently AI** | Data and model drift detection | Open-source, HTML reports, integrates with BigQuery |
| **Sentry** | Error tracking (FE + BE) | Real-time alerts, release tracking, source map upload |
| **Cloud Logging** | Centralized logs | Native to GCP, exports to BigQuery |
| **Cloud Monitoring** | SLO and alert policy | Uptime checks, custom metrics, integration with Discord |
| **Looker Studio** | Dashboarding | Free, BigQuery native, shareable URLs |
| **Discord webhook** | Team alerting | Free, low-friction, supports rich embeds |

### 3.8 Quality and Security

| Tool | Purpose | Why chosen |
|---|---|---|
| **Ruff** | Python lint + format | Replaces flake8 + black + isort, 10-100x faster |
| **ESLint + Prettier** | JS/TS lint + format | Industry standard |
| **pytest + pytest-cov** | Python test framework | De-facto standard |
| **Vitest** | Frontend test framework | Fast, Vite-based |
| **Bandit** | Python SAST | Catches common security issues |
| **Trivy** | Container and filesystem CVE scan | Fast, covers OS + lang packages |
| **Hadolint** | Dockerfile best-practices linter | Catches common Dockerfile mistakes |
| **Lighthouse CI** | Frontend performance gate | Industry-standard performance audit |
| **Gitleaks** | Secret leak detection | Prevent credential commits |

### 3.9 What we deliberately do NOT use

| Rejected | Reason |
|---|---|
| Kubernetes / GKE | Overkill for team size and traffic |
| Airflow / Prefect | GitHub Actions sufficient for our cadence |
| Feature Store (Feast, Tecton) | Dataset is small and batch-only |
| Workload Identity Federation | Service Account JSON simpler for POC scope |
| MongoDB / Firestore | Relational data fits PostgreSQL well |
| Datadog / New Relic | Cost; Sentry + Cloud Monitoring cover our needs |
| Kafka / Pub/Sub | No real-time stream requirement |

---

## 4. Repository Structure

```
mlops-project/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                  Person 1 owns
│   │   ├── ct-train.yml            Person 2 owns
│   │   ├── db-migrate.yml          Person 3 owns
│   │   ├── cd-backend.yml          Person 3 owns
│   │   ├── cd-frontend.yml         Person 3 owns
│   │   ├── monitor.yml             Person 4 owns
│   │   └── docs.yml                existing (mkdocs)
│   ├── CODEOWNERS
│   ├── pull_request_template.md
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       ├── drift_alert.md
│       └── feature_request.md
│
├── backend/                        SHARED (FastAPI app)
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── predict.py
│   │   │   ├── history.py
│   │   │   └── metrics.py
│   │   ├── schemas.py              Pydantic models
│   │   ├── deps.py                 dependencies (DB, Redis, model)
│   │   └── middleware.py           CORS, auth, rate limit
│   ├── db/
│   │   ├── models.py               SQLAlchemy ORM
│   │   ├── session.py              async session
│   │   └── migrations/             Alembic versions
│   ├── services/
│   │   ├── model_loader.py         load from GCS to /tmp
│   │   ├── prediction_service.py
│   │   └── cache_service.py
│   ├── tests/
│   │   ├── test_api.py
│   │   ├── test_db.py
│   │   └── test_cache.py
│   ├── app.py                      FastAPI entrypoint
│   ├── alembic.ini
│   └── requirements-serve.txt
│
├── frontend/                       SHARED (Next.js app)
│   ├── app/
│   │   ├── page.tsx                landing
│   │   ├── predict/page.tsx        form UI
│   │   ├── history/page.tsx        past predictions
│   │   ├── monitor/page.tsx        drift dashboard
│   │   └── api/                    edge functions
│   ├── components/
│   │   └── ui/                     shadcn components
│   ├── lib/
│   │   ├── api.ts                  API client
│   │   └── auth.ts
│   ├── tests/
│   │   ├── unit/
│   │   └── e2e/
│   ├── package.json
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   └── vercel.json
│
├── ml/                             SHARED (ML pipeline)
│   ├── steps/
│   │   ├── ingest.py
│   │   ├── clean.py
│   │   ├── validate.py             Pandera schemas
│   │   ├── train.py
│   │   └── predict.py
│   ├── main.py                     orchestrator
│   ├── config.yml                  hyperparameters
│   ├── tests/
│   │   ├── test_clean.py
│   │   ├── test_train.py
│   │   └── test_validate.py
│   └── requirements-train.txt
│
├── monitoring/                     SHARED
│   ├── evidently_report.py
│   ├── drift_threshold.yml
│   ├── queries/                    BigQuery SQL
│   └── notebooks/
│       └── monitor.ipynb
│
├── infra/                          Person 4 owns
│   ├── cloud-run-dev.yaml
│   ├── cloud-run-prod.yaml
│   ├── gcs-bucket-setup.sh
│   ├── cloudsql-setup.sh
│   ├── bigquery-schema.sql
│   ├── iam-roles.md
│   └── secret-manager-setup.sh
│
├── docs/                           SHARED
│   ├── MLOPS_PIPELINE.md           THIS FILE
│   ├── diagrams/
│   │   ├── architecture.mmd
│   │   ├── pillar-ci.mmd
│   │   ├── pillar-ct.mmd
│   │   ├── pillar-cd.mmd
│   │   └── pillar-cm.mmd
│   ├── adr/                        Architecture Decision Records
│   ├── runbook.md
│   └── mlops.jpg
│
├── data/                           DVC-tracked
├── models/                         DVC-tracked
├── docker-compose.yml              local dev (postgres + redis)
├── dockerfile                      multi-stage
├── dvc.yaml                        pipeline stages
├── .dvc/config                     GCS remote
├── .pre-commit-config.yaml
├── pyproject.toml                  ruff, pytest config
├── mkdocs.yml
├── makefile
├── .gitignore
├── .dockerignore
├── LICENSE
└── README.md
```

---

## 5. Branching Strategy and Environments

We use a **two-branch deployment model**: `dev` for staging, `prod` for production. The `main` branch is GitHub's default for clones and README display only, kept in sync with `prod` post-merge.

### Branch Model

```
prod          production environment, protected
 │            requires 2 reviewers + all checks pass
 │            push triggers CD to production
 │
 │   promote via PR (dev -> prod)
 │
dev           staging environment, protected, integration trunk
 │            requires 1 reviewer + all checks pass
 │            push triggers CD to staging
 │
 │   PR from feat/*
 │
feat/*        feature branches, free push
              opens PR to dev when ready

main          GitHub default branch (clone + README display only)
              auto-mirrored from prod post-merge, no direct work
```

### Promotion Flow

```
feat/your-feature  --PR-->  dev  --PR (promote)-->  prod
                            |                       |
                            v                       v
                       staging env            production env
                       (auto deploy)          (manual approval)
```

### Environment Mapping

| Branch | GitHub Environment | Backend deploy | Frontend deploy | Database |
|---|---|---|---|---|
| `feat/*` | none | local docker only | none | local docker-compose |
| `dev` | `development` | Cloud Run `insurance-api-dev` (auto) | Vercel Preview | Cloud SQL `app_dev` |
| `prod` | `production` | Cloud Run `insurance-api-prod` (approval) | Vercel Production | Cloud SQL `app_prod` |
| `main` | none | none (display only) | none (display only) | none |
| PR | none | none | Vercel Preview per PR | none |

### Branch Protection Rules

**`prod`** branch:
- Require 2 approving reviews
- Dismiss stale reviews on new commit
- Require status checks: `ci.yml` all jobs
- Require branches to be up to date
- Require linear history
- Disallow force push
- Restrict who can push (only via PR from `dev`)

**`dev`** branch:
- Require 1 approving review
- Require status checks: `ci.yml` lint + test + security
- Require branches to be up to date
- Allow merge from `feat/*` PRs

**`main`** branch:
- Mirror-only target, auto-synced from `prod` post-merge (no direct work)
- Disallow force push

### Why this model

| Reason | Benefit |
|---|---|
| Separate `dev` and `prod` branches | Each branch maps 1-to-1 with a runtime environment — clear mental model |
| `main` kept as GitHub default | Clones and README display correctly; no breaking convention |
| PR `dev -> prod` is the promotion gate | Production deploys are explicit, reviewable, and revertable |
| `feat/*` always targets `dev` | Prevents accidental direct PR to prod |

---

## 6. Team Task Division

### 6.1 Ownership Model

We split **personal ownership** of CI/CD pipelines per person, while **application code is shared**.

```
PERSONAL OWNERSHIP                    SHARED OWNERSHIP
(pipelines)                           (code)

Person 1  →  CI                       backend/   all 4 contribute
Person 2  →  CT                       frontend/  all 4 contribute
Person 3  →  CD (Backend + Frontend)  ml/        all 4 contribute
Person 4  →  CM + Infrastructure      tests/     all 4 contribute
                                      docs/      all 4 contribute
```

### 6.2 Per-Person Detail

#### Person 1 — CI Owner

**Tagline**: "Owner code quality and merge gate"

**Files owned**:
- `.github/workflows/ci.yml`
- `.github/workflows/security-scan.yml` (if separated)
- `pyproject.toml` (ruff config)
- `pytest.ini` / `.coveragerc`
- `.pre-commit-config.yaml`
- `frontend/.eslintrc.json`
- `frontend/vitest.config.ts`

**Skills needed**: GitHub Actions YAML, pytest, ruff, security scanning concepts

**Deliverables**:
- Every PR passes 9 quality gates before merge
- Coverage badge live in README at >= 70%
- Zero broken commit reaches `dev` or `prod`
- Security alerts triaged within 24 hours

**KPI for evaluation**:
- PR rejected by CI must have actionable error message
- CI duration kept under 8 minutes
- False-positive rate of security scans below 10%

---

#### Person 2 — CT Owner

**Tagline**: "Owner model training pipeline and reproducibility"

**Files owned**:
- `.github/workflows/ct-train.yml`
- `ml/validate.py` (Pandera schemas)
- `dvc.yaml`
- `scripts/promote_model.py`
- `scripts/gen_model_card.py`
- `ml/config.yml` (curator, not exclusive editor)

**Skills needed**: Python, scikit-learn, MLflow, DVC, gcloud, statistics for model comparison

**Deliverables**:
- Reproducible training via `dvc repro` locally and in CI
- At least 3 model variants compared and tracked in MLflow
- Auto-promotion logic (champion vs challenger) working
- Model card auto-generated per training run

**KPI for evaluation**:
- Training pipeline success rate >= 95%
- Time from data update to new model in Registry under 30 minutes
- Model version traceable to data hash + git SHA + config

---

#### Person 3 — CD Owner

**Tagline**: "Owner deployment automation and runtime stability"

**Files owned**:
- `.github/workflows/cd-backend.yml`
- `.github/workflows/cd-frontend.yml`
- `.github/workflows/db-migrate.yml`
- `dockerfile` (multi-stage)
- `.dockerignore`
- `docker-compose.yml` (local dev)
- `frontend/vercel.json`
- `infra/cloud-run-dev.yaml`
- `infra/cloud-run-prod.yaml`
- `backend/alembic.ini` and migration files

**Skills needed**: Docker, gcloud, Vercel CLI, Alembic, networking basics

**Deliverables**:
- Backend deployed to 2 environments (Cloud Run dev + prod)
- Frontend deployed to 2 environments (Vercel preview + prod)
- Per-PR preview URL for frontend
- Canary rollout 10% then 100% with auto-rollback on SLO breach
- Database migration runs before backend deploy

**KPI for evaluation**:
- Deployment success rate >= 99%
- Rollback time under 2 minutes
- Zero downtime deploys
- Image size under 500MB, bundle under 250KB

---

#### Person 4 — CM Owner + Infrastructure Lead

**Tagline**: "Owner observability, infra setup, team coordination"

**Files owned**:
- `.github/workflows/monitor.yml`
- `.github/workflows/alert-drift.yml`
- `monitoring/evidently_report.py`
- `monitoring/drift_threshold.yml`
- `monitoring/queries/` (BigQuery SQL)
- `infra/gcs-bucket-setup.sh`
- `infra/cloudsql-setup.sh`
- `infra/bigquery-schema.sql`
- `infra/iam-roles.md`
- `infra/secret-manager-setup.sh`
- `docs/runbook.md`
- `docs/MLOPS_PIPELINE.md` (curator)
- GitHub repo settings (branch protection, CODEOWNERS, Environments)

**Skills needed**: Evidently, BigQuery SQL, gcloud, IAM, dashboarding, technical writing

**Deliverables**:
- Daily drift report HTML uploaded to GCS
- Looker Studio dashboard live with 5 charts minimum
- Sentry projects configured (FE + BE) with release tracking
- Auto-trigger CT workflow when drift > 0.3
- Complete runbook for incident response
- All cloud resources provisioned and documented

**KPI for evaluation**:
- Drift detection has zero misses in test scenarios
- Dashboard refresh frequency under 15 minutes
- Mean time to alert under 5 minutes
- Documentation completeness verified by other team members

---

### 6.3 RACI Matrix

| Component / Activity | P1 (CI) | P2 (CT) | P3 (CD) | P4 (CM) |
|---|---|---|---|---|
| `ci.yml` workflow | **R** | C | C | C |
| `ct-train.yml` workflow | C | **R** | I | C |
| `db-migrate.yml` workflow | C | I | **R** | C |
| `cd-backend.yml` workflow | C | I | **R** | C |
| `cd-frontend.yml` workflow | C | I | **R** | C |
| `monitor.yml` workflow | I | C | I | **R** |
| GCS bucket + IAM setup | I | C | C | **R** |
| Cloud SQL setup | I | C | C | **R** |
| GitHub Secrets management | C | C | C | **R** |
| Repository settings | I | I | I | **R** |
| ML training code (`ml/`) | shared | shared | shared | shared |
| Backend code (`backend/`) | shared | shared | shared | shared |
| Frontend code (`frontend/`) | shared | shared | shared | shared |
| Unit + integration tests | shared | shared | shared | shared |
| Documentation | shared | shared | shared | shared |
| Code review (cross-folder) | shared | shared | shared | shared |

**R** = Responsible (does the work) · **C** = Consulted (reviews / advises) · **I** = Informed (kept up to date)

### 6.4 Backup Buddy System

If owner is unavailable, the buddy takes over their pipeline:

| Owner | Buddy |
|---|---|
| Person 1 (CI) | Person 3 (similar GH Actions skills) |
| Person 2 (CT) | Person 4 (similar Python/data skills) |
| Person 3 (CD) | Person 1 (similar GH Actions skills) |
| Person 4 (CM) | Person 2 (similar Python/data skills) |

Each owner **must** document their pipeline in `docs/` so buddy can take over within 1 hour.

### 6.5 Sprint Plan (4 Weeks)

| Week | Person 1 | Person 2 | Person 3 | Person 4 |
|---|---|---|---|---|
| **1** | Setup ci.yml lint + test base | Refactor `ml/` + DVC pipeline | Restructure backend + Dockerfile | GCP setup, repo settings |
| **2** | Add security + DB migration check | Train 3 models, MLflow remote | API endpoints + Docker push CI | Cloud SQL + Redis + BQ schema |
| **3** | Coverage gate + PR reports | Champion/challenger + promote | Cloud Run deploy dev + Vercel preview | Evidently scheduled + Looker dashboard |
| **4** | Hardening + CI duration optimize | Tuning + model card final | Prod approval + canary + rollback | Alerting + runbook + handover |

### 6.6 Collaboration Mechanics

- **Daily async standup** in Discord `#standup` (5 min: yesterday, today, blocker)
- **Weekly sync** Monday 60 min (demo, integration check, replan)
- **Pair programming** Tuesday (P1+P2: ML/CI integration) and Thursday (P3+P4: CD/CM integration)
- **PR review SLA**: under 24 hours, minimum 1 approval, cross-folder reviewer required
- **Decision log**: every architectural decision in `docs/adr/NNNN-title.md`

---

## 7. Pillar 1 — CI : Continuous Integration

### 7.1 Purpose

Ensure every Pull Request is safe to merge into `dev` or `prod`. Block bad code from reaching the protected branches.

### 7.2 Trigger Conditions

| Trigger | Condition |
|---|---|
| `pull_request` | any PR opened or updated targeting `dev` or `prod` |
| `push` | any push to `feat/*` branches |

### 7.3 Job-by-Job Detail

#### Job 1: Setup Environment

| Step | Tool | Output |
|---|---|---|
| Checkout | `actions/checkout@v4` with `fetch-depth: 0` | full git history available |
| Setup Python | `actions/setup-python@v5` version 3.10, cache pip | Python ready |
| Setup Node | `actions/setup-node@v4` version 20, cache pnpm | Node ready |
| Install deps | `pnpm install --frozen-lockfile` + `pip install -r requirements-dev.txt` | dependencies installed |

#### Job 2: Code Quality

| Step | Tool | Command |
|---|---|---|
| Python lint | Ruff | `ruff check .` |
| Python format | Ruff | `ruff format --check .` |
| JS/TS lint | ESLint | `pnpm lint` |
| JS/TS format | Prettier | `pnpm format:check` |

**Failure handling**: PR annotated with diff suggestions, status check fails.

#### Job 3: Test Suite

| Step | Tool | Command |
|---|---|---|
| Backend tests | pytest | `pytest tests/ -v` |
| Coverage gate | pytest-cov | `--cov-fail-under=70` |
| Frontend tests | Vitest | `pnpm test` |
| Coverage upload | Codecov | `codecov/codecov-action@v4` |

**Failure handling**: PR comment lists failed tests, status check fails.

#### Job 4: Schema Validation

| Step | Tool | Purpose |
|---|---|---|
| Pandera dry-run | Pandera | validate ML data schemas can load |
| Pydantic import check | Pydantic | validate API schemas valid |
| OpenAPI diff check | scripts/export_openapi.py | ensure committed `openapi.json` matches generated |

#### Job 5: Database Migration Check

| Step | Tool | Purpose |
|---|---|---|
| Spin postgres | `postgres:16-alpine` service container | local DB for test |
| Run migrations | `alembic upgrade head` | apply all pending |
| Verify clean state | `alembic check` | no pending migrations after apply |
| ER diagram | `eralchemy` | upload as artifact for review |

#### Job 6: Security Scan

| Step | Tool | Coverage |
|---|---|---|
| Python SAST | Bandit | common security issues (SQL injection, hardcoded keys) |
| Filesystem CVE | Trivy | OS packages + Python deps |
| Pip vulnerabilities | Safety | known CVE in Python deps |
| NPM audit | pnpm | known CVE in JS deps |
| Secret scan | Gitleaks | leaked credentials in diff |

**Failure handling**: any HIGH or CRITICAL finding blocks merge, opens security issue.

#### Job 7: Build Validation

| Step | Tool | Purpose |
|---|---|---|
| Docker build builder | Docker buildx | validate builder stage |
| Docker build runtime | Docker buildx + GHA cache | validate runtime stage |
| Dockerfile lint | Hadolint | best-practices check |
| Image size gate | shell | fail if > 500 MB |
| Next.js build | `pnpm build` | validate FE builds |
| Bundle size gate | preact compressed-size-action | fail if > 250 KB gzip first load |

#### Job 8: Integration Smoke Test

| Step | Tool | Purpose |
|---|---|---|
| Spin stack | docker-compose | API + Postgres + Redis |
| Wait healthcheck | wait-for-it | ensure ready |
| Test `GET /` | curl | expect 200 |
| Test `POST /predict` | curl with `samples.json` | expect predicted_class field |
| Test `GET /metrics` | curl | expect Prometheus format |
| Teardown | docker-compose | clean up |

#### Job 9: PR Report

| Step | Tool | Output |
|---|---|---|
| Coverage comment | sticky-pull-request-comment | coverage delta posted |
| Lint annotations | reviewdog | inline diff suggestions |
| Bundle size diff | preact compressed-size-action | size change posted |
| Commit status | GitHub API | green checkmark on commit |

### 7.4 Outputs

- PR status checks: 9 required, all must pass
- Coverage badge updated
- Security alerts created if needed
- ER diagram and OpenAPI artifacts available for review

### 7.5 Tools Summary

`actions/checkout` · `actions/setup-python` · `actions/setup-node` · `pnpm` · `Ruff` · `ESLint` · `Prettier` · `pytest` · `pytest-cov` · `Codecov` · `Vitest` · `Pandera` · `Pydantic` · `Alembic` · `eralchemy` · `Bandit` · `Trivy` · `Safety` · `Gitleaks` · `Docker buildx` · `Hadolint` · `Lighthouse CI` · `docker-compose` · `curl`

---

## 8. Pillar 2 — CT : Continuous Training

### 8.1 Purpose

Automatically retrain the model when data, config, or schedule triggers indicate it should. Compare new model against production champion. Promote only if better. Push to GCS via DVC. Tag a release.

### 8.2 Trigger Conditions

| Trigger | Condition |
|---|---|
| `workflow_dispatch` | manual click in GitHub UI |
| `schedule` | cron `0 2 * * 1` (Monday 02:00 WIB) |
| `push` to `prod` | paths include `ml/config.yml` or `ml/**` or `dvc.lock` |
| `repository_dispatch` | event type `drift-retrain` from CM workflow |

### 8.3 Job-by-Job Detail

#### Job 1: Authentication

| Step | Tool | Purpose |
|---|---|---|
| Checkout | `actions/checkout@v4` | get code |
| GCP auth | `google-github-actions/auth@v2` | use `GCP_SA_KEY` secret |
| Setup gcloud | `google-github-actions/setup-gcloud@v2` | configure CLI |
| Verify access | `gsutil ls gs://pso-mlops-dvc-sandy` | sanity check |

#### Job 2: Data Acquisition

| Step | Tool | Purpose |
|---|---|---|
| Setup Python | `actions/setup-python@v5` | Python ready |
| Install DVC | `pip install dvc dvc-gs` | DVC with GCS support |
| Pull data | `dvc pull --remote gcsremote` | fetch train, test, production CSVs |
| Verify integrity | `md5sum` comparison | match `.dvc` files |
| Log row counts | echo to `$GITHUB_STEP_SUMMARY` | visibility |

#### Job 3: Data Validation

| Step | Tool | Purpose |
|---|---|---|
| Validate train | `python ml/validate.py train.csv` | Pandera schema check |
| Validate test | `python ml/validate.py test.csv` | Pandera schema check |
| Schema drift | compare against last run | detect column changes |
| Distribution sanity | min/max/null per feature | catch obvious issues |

**Failure**: abort training, create GitHub Issue with `data-quality` label.

#### Job 4: Model Training

| Step | Tool | Purpose |
|---|---|---|
| Install deps | `pip install -r ml/requirements-train.txt` | scikit-learn, MLflow, imblearn |
| Set MLflow URI | env `MLFLOW_TRACKING_URI` | point to remote tracking server |
| Set MLflow token | env `MLFLOW_TRACKING_TOKEN` | from `MLFLOW_TOKEN` secret |
| Run training | `python ml/main.py` | runs `train_with_mlflow()` |
| Log params | `mlflow.log_params` | from `config.yml` |
| Log metrics | `mlflow.log_metric` | accuracy, ROC AUC, precision, recall |
| Log model | `mlflow.sklearn.log_model` | artifact upload to GCS |
| Set tags | `mlflow.set_tag` | git SHA, branch, trigger type |

#### Job 5: Model Registration

| Step | Tool | Purpose |
|---|---|---|
| Register | `mlflow.register_model` | create `insurance_model` entry |
| Set stage | `client.transition_model_version_stage` | None → Staging |
| Add description | API call | auto changelog from commit messages |

#### Job 6: Champion vs Challenger

| Step | Tool | Purpose |
|---|---|---|
| Fetch current Production | MLflow API | get champion model |
| Inference both | scikit-learn | predict on held-out test set |
| Compare metrics | manual | accuracy, ROC AUC, latency |
| Statistical test | scipy / sklearn | McNemar test or paired t-test |

**Decision**: if challenger is better by >= 1% on accuracy AND p-value < 0.05, promote. Otherwise, keep in Staging and notify team.

#### Job 7: Promotion

| Step | Tool | Purpose |
|---|---|---|
| Archive previous Production | MLflow API | stage → Archived |
| Promote challenger | MLflow API | stage → Production, `archive_existing_versions=True` |
| Generate model card | `scripts/gen_model_card.py` | upload as artifact |

#### Job 8: Artifact Versioning

| Step | Tool | Purpose |
|---|---|---|
| Download model | MLflow API | get model.pkl |
| DVC add | `dvc add models/model.pkl` | update `models.dvc` |
| DVC push | `dvc push --remote gcsremote` | upload to GCS |
| Git config bot | shell | set `github-actions[bot]` user |
| Git commit | `chore(model): retrain model-v{n}` | commit `.dvc` files |
| Git push | `git push origin prod` | trigger CD downstream |

#### Job 9: GitHub Release

| Step | Tool | Purpose |
|---|---|---|
| Bump version | shell | `model-v$(date +%Y%m%d)-{run_number}` |
| Create release | `softprops/action-gh-release` | tag, title, body with metrics |
| Attach model card | upload asset | for traceability |
| Attach metrics JSON | upload asset | machine-readable |

#### Job 10: Notify and Chain

| Step | Tool | Purpose |
|---|---|---|
| Discord notify | webhook | embed with metric diff vs previous |
| Trigger CD | `gh workflow run cd-backend.yml` | downstream deployment |
| Update summary | `$GITHUB_STEP_SUMMARY` | training overview |

### 8.4 Outputs

- New model version in MLflow Registry stage `Production`
- New model file in GCS `dvc-store/`
- GitHub Release with model card and metrics
- `cd-backend.yml` workflow auto-triggered
- Team notified in Discord

### 8.5 Tools Summary

`actions/checkout` · `google-github-actions/auth` · `google-github-actions/setup-gcloud` · `gsutil` · `pip` · `DVC` · `dvc-gs` · `md5sum` · `Pandera` · `scikit-learn` · `imblearn (SMOTE)` · `MLflow` · `scipy` · `softprops/action-gh-release` · `gh CLI` · `Discord webhook`

---

## 9. Pillar 3a — CD Backend

### 9.1 Purpose

Deploy FastAPI backend container to Cloud Run with database migration, canary traffic shift, health check, and automatic rollback.

### 9.2 Trigger Conditions

| Trigger | Behavior |
|---|---|
| `push` to `dev` | auto-deploy to `insurance-api-dev` |
| `push` to `prod` | requires Manual Approval Gate, then deploy to `insurance-api-prod` |
| `workflow_dispatch` | manual deploy with optional rollback flag |
| `workflow_call` from `ct-train.yml` | auto-deploy after new model promoted |

### 9.3 Manual Approval Gate

- GitHub Environment: `production`
- Required reviewers: 2
- Wait timer: 5 minutes
- Secrets scope: production-only credentials

### 9.4 Job-by-Job Detail

#### Job 1: Authentication

| Step | Tool |
|---|---|
| Checkout | `actions/checkout@v4` |
| GCP auth | `google-github-actions/auth@v2` |
| GHCR login | `docker/login-action@v3` |
| Configure docker | `gcloud auth configure-docker` |

#### Job 2: Fetch Model Artifact

| Step | Tool | Purpose |
|---|---|---|
| Install DVC | `pip install dvc dvc-gs` | tool ready |
| Pull model | `dvc pull models/model.pkl --remote gcsremote` | get latest model |
| Verify loadable | `python -c "import joblib; joblib.load('models/model.pkl')"` | sanity check |
| Read MODEL_VERSION | MLflow API | get version tag from Registry |

#### Job 3: Database Migration

| Step | Tool | Purpose |
|---|---|---|
| Cloud SQL Proxy | `cloud-sql-proxy --port 5432` | secure connection |
| Install Alembic | `pip install alembic asyncpg` | tool ready |
| Show current | `alembic current` | log current revision |
| Show history | `alembic history --verbose` | log pending migrations |
| Apply | `alembic upgrade head` | run migrations |
| Verify | `alembic check` | ensure no drift |

**Failure handling**: `alembic downgrade -1`, halt deploy, EXIT 1.

#### Job 4: Docker Build and Push

| Step | Tool | Purpose |
|---|---|---|
| Setup buildx | `docker/setup-buildx-action@v3` | enable build cache |
| Generate tags | `docker/metadata-action@v5` | `api:{env}-{sha}` and `api:{env}-latest` |
| Build and push | `docker/build-push-action@v5` | multi-stage with GHA cache |
| Trivy scan | `aquasecurity/trivy-action` | HIGH/CRITICAL only |
| Cosign sign | `sigstore/cosign-installer` | keyless OIDC signature |

#### Job 5: Cloud Run Deploy

| Setting | Value (dev) | Value (prod) |
|---|---|---|
| Service name | `insurance-api-dev` | `insurance-api-prod` |
| Region | `asia-southeast1` | `asia-southeast1` |
| Min instances | 0 | 1 |
| Max instances | 5 | 20 |
| Memory | 1 Gi | 2 Gi |
| CPU | 1 | 2 |
| Concurrency | 80 | 80 |
| Execution env | gen2 | gen2 |
| Cloud SQL | `app_dev` | `app_prod` |
| VPC connector | `mlops-conn` (for Redis) | `mlops-conn` |

**Env vars** (from Secret Manager):
- `APP_ENV` (dev or prod)
- `MODEL_VERSION` (from Registry)
- `GCS_MODEL_URI`
- `DATABASE_URL` (from secret)
- `REDIS_URL` (from secret)
- `MLFLOW_URI`
- `SENTRY_DSN` (from secret)

#### Job 6: Canary Traffic Shift

| Step | Tool | Purpose |
|---|---|---|
| Deploy no-traffic | `gcloud run deploy --no-traffic` | create revision |
| Shift 10% | `gcloud run services update-traffic --to-revisions={rev}=10` | canary |
| Wait | `sleep 300` | observe 5 min |
| Query metrics | Cloud Monitoring API | error rate, p95 latency |

**Decision**: if canary metrics within SLO (error < 1%, p95 < 500 ms), promote. Else rollback.

#### Job 7: Promote to 100%

| Step | Tool |
|---|---|
| Shift 100% | `gcloud run services update-traffic --to-revisions={rev}=100` |
| Tag revision | `gcloud run services update-traffic --update-tags v{n}={rev}` |

#### Job 8: Post-Deploy Verification

| Step | Tool | Test |
|---|---|---|
| Get URL | `gcloud run services describe` | extract service URL |
| Health check | `curl GET /` | expect 200 + `model_loaded: true` |
| Predict smoke | `curl POST /predict` | with `samples.json`, expect prediction |
| Metrics check | `curl GET /metrics` | expect Prometheus format |
| E2E suite | `pytest tests/e2e/ --base-url $URL` | full integration |

#### Job 9: Notify

| Step | Tool |
|---|---|
| Discord webhook | `tsickert/discord-webhook` |
| Sentry release | `getsentry/action-release@v1` |
| Job summary | echo to `$GITHUB_STEP_SUMMARY` |

### 9.5 Outputs

- Cloud Run service live at `https://insurance-api-{env}-xxx.run.app`
- 100% traffic on new revision
- Sentry release tracked
- Team notified

### 9.6 Tools Summary

`actions/checkout` · `google-github-actions/auth` · `docker/login-action` · `docker/setup-buildx-action` · `docker/metadata-action` · `docker/build-push-action` · `Trivy` · `Cosign` · `DVC` · `MLflow API` · `Cloud SQL Proxy` · `Alembic` · `asyncpg` · `gcloud run` · `Cloud Monitoring API` · `curl` · `pytest` · `Sentry CLI` · `Discord webhook`

---

## 10. Pillar 3b — CD Frontend

### 10.1 Purpose

Deploy Next.js frontend to Vercel with Lighthouse performance gate, E2E smoke test, and per-PR preview.

### 10.2 Trigger Conditions

| Trigger | Behavior |
|---|---|
| `push` to `dev` | auto-deploy to Vercel Development |
| `push` to `prod` | requires Manual Approval Gate, then Production |
| `pull_request` | per-PR preview deployment |

### 10.3 Job-by-Job Detail

#### Job 1: Setup

| Step | Tool |
|---|---|
| Checkout | `actions/checkout@v4` |
| pnpm setup | `pnpm/action-setup@v3` version 9 |
| Node setup | `actions/setup-node@v4` version 20, cache pnpm |
| Install | `pnpm install --frozen-lockfile` |

#### Job 2: Pre-build Quality

| Step | Tool | Command |
|---|---|---|
| TypeScript | `tsc` | `pnpm tsc --noEmit` |
| Lint | ESLint | `pnpm lint` |
| Unit tests | Vitest | `pnpm test:unit` |
| Component tests | Testing Library | `pnpm test:component` |

#### Job 3: Vercel Env Pull

| Step | Tool | Purpose |
|---|---|---|
| Install CLI | `npm i -g vercel@latest` | tool ready |
| Pull env | `vercel pull --yes --environment={target}` | get env vars |
| Verify link | check `.vercel/project.json` | sanity check |
| Inject API URL | env override | environment-specific |

#### Job 4: Build

| Step | Tool | Purpose |
|---|---|---|
| Vercel build | `vercel build --prod` (or omit `--prod` for preview) | invokes `next build` |
| Output | `.vercel/output/` | static + functions + edge |
| Bundle size gate | `preactjs/compressed-size-action` | fail if > 250 KB gzip |

#### Job 5: Lighthouse CI

| Step | Tool | Threshold |
|---|---|---|
| Lighthouse | `treosh/lighthouse-ci-action@v11` | run audit |
| URLs tested | `/`, `/predict`, `/history` | 3 critical pages |
| Performance | gate | >= 90 |
| Accessibility | gate | >= 95 |
| Best practices | gate | >= 95 |
| SEO | gate | >= 90 |

#### Job 6: Deploy

| Step | Tool | Purpose |
|---|---|---|
| Vercel deploy | `vercel deploy --prebuilt --prod` (or omit `--prod`) | upload artifacts |
| Capture URL | shell | `VERCEL_URL=$(...)` |
| Alias domain | `vercel alias $URL insurance.example.com` | prod only |

#### Job 7: E2E Smoke

| Step | Tool | Purpose |
|---|---|---|
| Install browsers | `playwright install chromium` | E2E runtime |
| Run tests | `pnpm test:e2e` with `BASE_URL=$VERCEL_URL` | scenarios |
| Test scenarios | Playwright | landing, form submit, history table, monitor chart |
| Upload trace on fail | `actions/upload-artifact@v4` | for debugging |

**Failure**: `vercel rollback`, EXIT 1.

#### Job 8: Notify

| Step | Tool |
|---|---|
| PR comment | `marocchino/sticky-pull-request-comment` with preview URL |
| Discord | webhook |
| Sentry release FE | `getsentry/action-release@v1` |

### 10.4 Outputs

- Vercel deployment live at preview URL or production domain
- PR commented with preview URL
- Sentry release tracked

### 10.5 Tools Summary

`actions/checkout` · `pnpm/action-setup` · `actions/setup-node` · `TypeScript` · `ESLint` · `Vitest` · `Testing Library` · `Vercel CLI` · `Next.js` · `preactjs/compressed-size-action` · `treosh/lighthouse-ci-action` · `Playwright` · `Sentry CLI` · `Discord webhook`

---

## 11. Pillar 4 — CM : Continuous Monitoring

### 11.1 Purpose

Daily detect data drift, target drift, and model performance degradation. Auto-trigger retraining when drift exceeds threshold. Also operate realtime layer for runtime errors.

### 11.2 Trigger Conditions

| Trigger | Condition |
|---|---|
| `schedule` | cron `0 6 * * *` (daily 06:00 WIB) |
| `workflow_dispatch` | manual run |
| `repository_dispatch` | realtime alert from Cloud Monitoring |

### 11.3 Job-by-Job Detail

#### Job 1: Setup

| Step | Tool |
|---|---|
| Checkout | `actions/checkout@v4` |
| GCP auth | `google-github-actions/auth@v2` |
| Setup Python | `actions/setup-python@v5` |
| Install | `pip install evidently pandas pyarrow google-cloud-bigquery google-cloud-storage` |

#### Job 2: Fetch Production Data

| Step | Tool | Purpose |
|---|---|---|
| BigQuery query | `bq` CLI | last 24h prediction logs from `mlops.prediction_logs` |
| Flatten JSON | pandas | unpack `input_payload` JSONB |
| Save artifact | parquet | upload as workflow artifact |

#### Job 3: Fetch Reference Data

| Step | Tool | Purpose |
|---|---|---|
| DVC pull | `dvc pull data/train.csv` | reference training set |
| Load | pandas | DataFrame |
| Sample | stratified | match production size |

#### Job 4: Drift Analysis

| Step | Tool | Output |
|---|---|---|
| Data drift | Evidently `DataDriftPreset` | per-feature drift score |
| Target drift | Evidently `TargetDriftPreset` | prediction distribution diff |
| Data quality | Evidently `DataQualityPreset` | null ratio, duplicates, outliers |
| Save HTML | `report.save_html()` | shareable report |
| Extract JSON | `report.as_dict()` | machine-readable metrics |

#### Job 5: Store Results

| Step | Tool | Destination |
|---|---|---|
| Upload HTML | `gsutil cp` | `gs://.../reports/{date}.html` |
| Signed URL | `gsutil signurl` | 7-day public access |
| Insert metrics | BigQuery `INSERT` | `mlops.drift_metrics` |
| Refresh Looker | Looker API | clear cache |

#### Job 6: Model Performance Tracking

| Step | Tool | Purpose |
|---|---|---|
| Join feedback | BigQuery SQL | match predictions with actual labels (if available) |
| Compute metrics | `sklearn.metrics` | accuracy, precision, recall, ROC AUC |
| Insert to BQ | `INSERT` | `mlops.model_performance` |

#### Decision 1: Drift Threshold

```
IF data_drift_score > 0.3
   OR target_drift_score > 0.2
   OR accuracy_drop > 5%
THEN proceed to Job 7 (Alert and Retrain)
ELSE skip
```

#### Job 7: Alert and Trigger Retrain

| Step | Tool | Purpose |
|---|---|---|
| Create issue | `actions/github-script@v7` | title, label `drift-alert priority-high`, body with report URL |
| Discord embed | webhook | mention `@ml-team` role |
| Email | `peter-evans/sendgrid-action` | to ml-leads list |
| Trigger CT | `peter-evans/repository-dispatch` | event type `drift-retrain` |
| Custom metric | Cloud Monitoring API | fire alert policy |

#### Decision 2: Runtime SLO

```
IF Sentry error rate > 1%
   OR p95 latency > 500 ms
THEN proceed to Job 8 (SRE Alert)
ELSE skip
```

#### Job 8: SRE Alert (prod only)

| Step | Tool |
|---|---|
| PagerDuty incident | API call |
| Discord on-call | webhook to `#on-call` |
| Auto-rollback PR | `gh pr create` | revert last deploy |

#### Job 9: Dashboard Refresh

| Step | Tool |
|---|---|
| Looker refresh | API call |
| Verify render | HTTP GET screenshot endpoint |

#### Job 10: Weekly Summary (Friday only)

| Step | Tool | Purpose |
|---|---|---|
| Aggregate 7 days | BigQuery SQL | avg drift, perf delta, error rate |
| Discord post | webhook to `#weekly` | summary |
| Job summary | `$GITHUB_STEP_SUMMARY` | links to reports |

### 11.4 Realtime Continuous Layer (parallel)

| Component | Purpose | Cadence |
|---|---|---|
| Sentry SDK | capture FE+BE errors | realtime |
| Cloud Logging + FluentBit | structured logs | realtime |
| Cloud Monitoring uptime | endpoint check | every 1 minute |
| Looker Studio | dashboard | auto-refresh 15 min |
| Cloud Monitoring alert policy | trigger Discord on SLO breach | realtime |

### 11.5 Outputs

- Daily HTML drift report on GCS, accessible via signed URL
- BigQuery `drift_metrics` and `model_performance` tables updated
- Looker dashboard refreshed
- GitHub Issue if drift detected
- Discord alert if drift or SLO breach
- CT workflow triggered automatically if drift exceeds threshold
- Weekly summary Friday

### 11.6 Tools Summary

`actions/checkout` · `google-github-actions/auth` · `BigQuery (bq CLI)` · `DVC` · `pandas` · `pyarrow` · `Evidently AI` · `gsutil` · `Looker Studio API` · `sklearn` · `actions/github-script` · `Discord webhook` · `SendGrid` · `peter-evans/repository-dispatch` · `Cloud Monitoring API` · `PagerDuty API` · `gh CLI` · `Sentry SDK` · `Cloud Logging` · `FluentBit`

---

## 12. Data Architecture

### 12.1 Storage Topology

| Store | Type | Purpose | Owner |
|---|---|---|---|
| GCS `pso-mlops-dvc-sandy` | object | data, models, reports, backups | Person 4 |
| GHCR | OCI registry | Docker images | Person 3 |
| Cloud SQL `app_prod`, `app_dev` | PostgreSQL 16 | application data | Person 3 |
| Cloud SQL `mlflow_prod` | PostgreSQL 16 | MLflow metadata backend | Person 2 |
| Memorystore Redis 7 | in-memory | cache, rate limit, session | Person 3 |
| BigQuery `mlops` dataset | analytics warehouse | logs, drift, performance | Person 4 |

### 12.2 GCS Bucket Layout

```
gs://pso-mlops-dvc-sandy/
├── dvc-store/                 DVC-managed data and models
├── mlflow-artifacts/          MLflow experiment artifacts
├── predictions-raw/           JSONL append-only request logs
│   └── 2026-05-25/
├── reports/                   Evidently HTML drift reports
│   └── 2026-05-25.html
└── backups/                   nightly DB dumps, 30-day retention
    └── app_prod_2026-05-25.sql.gz
```

### 12.3 PostgreSQL Schema

#### Database: `app_prod` (and `app_dev` mirror)

| Table | Purpose | Key columns |
|---|---|---|
| `users` | user accounts | id PK, email unique, password_hash, role, created_at |
| `predictions_history` | past predictions per user | id PK, user_id FK, input_payload JSONB, predicted_class, model_version, latency_ms, created_at INDEX |
| `audit_logs` | security audit trail | id PK, user_id FK, action, resource, ip_address, timestamp |
| `api_keys` | external API access | id PK, user_id FK, key_hash, name, last_used_at, revoked_at |

#### Database: `mlflow_prod`

| Table | Purpose |
|---|---|
| `experiments` | experiment metadata |
| `runs` | individual training runs |
| `metrics` | logged metrics per run |
| `params` | hyperparameters per run |
| `model_versions` | registered models with stages |

### 12.4 Redis Key Patterns

| Pattern | Type | TTL | Purpose |
|---|---|---|---|
| `pred:{hash}` | String (JSON) | 3600 s | cache hot prediction results |
| `rate:{apikey}:{hour}` | Sorted Set | 3600 s | sliding window rate limit |
| `session:{jwt_id}` | String | 86400 s | JWT blacklist on logout |
| `queue:retrain` | Stream | infinite | decouple drift event from CT trigger |

### 12.5 BigQuery Schema

| Table | Partitioning | Clustering | Purpose |
|---|---|---|---|
| `mlops.prediction_logs` | by `DATE(timestamp)` | by `env`, `model_version` | streaming insert from Cloud Run |
| `mlops.drift_metrics` | by `date` | by `feature` | daily Evidently output |
| `mlops.model_performance` | by `date` | by `model_version` | accuracy tracking over time |
| `mlops.api_metrics` | by `DATE(timestamp)` | by `endpoint` | export from Cloud Logging |

### 12.6 Data Flow Summary

```
Cloud Run BE  ─INSERT─→  PG app_prod (history, audit)
              ─SET────→  Redis (cache, rate limit)
              ─APPEND─→  GCS predictions-raw/
              ─emit──→   Sentry
              ─logs──→   Cloud Logging ──export──→  BigQuery api_metrics

GCS predictions-raw/  ──streaming load──→  BigQuery prediction_logs

CT workflow   ─push──→  GCS dvc-store/ (model)
              ─log───→  PG mlflow_prod (metadata)
              ─artifact→ GCS mlflow-artifacts/

CM workflow   ─read──→  BigQuery prediction_logs
              ─read──→  GCS train.csv (reference)
              ─write─→  BigQuery drift_metrics, model_performance
              ─upload→  GCS reports/

Looker Studio ─read──→  BigQuery (all 4 tables)
```

---

## 13. Secrets and IAM Management

### 13.1 GitHub Secrets

Stored in repo settings → Secrets and variables → Actions.

| Secret | Scope | Used by |
|---|---|---|
| `GCP_SA_KEY` | repo | all GCP-related workflows |
| `GCP_PROJECT_ID` | repo | all GCP-related workflows |
| `VERCEL_TOKEN` | environment `development` and `production` | cd-frontend.yml |
| `VERCEL_ORG_ID` | repo | cd-frontend.yml |
| `VERCEL_PROJECT_ID_DEV` | environment `development` | cd-frontend.yml |
| `VERCEL_PROJECT_ID_PROD` | environment `production` | cd-frontend.yml |
| `MLFLOW_TRACKING_URI` | repo | ct-train.yml |
| `MLFLOW_TOKEN` | repo | ct-train.yml |
| `DISCORD_WEBHOOK_CT` | repo | ct-train.yml |
| `DISCORD_WEBHOOK_CD` | repo | cd-backend.yml, cd-frontend.yml |
| `DISCORD_WEBHOOK_ALERT` | repo | monitor.yml |
| `SENTRY_DSN_BE` | environment | cd-backend.yml |
| `SENTRY_DSN_FE` | environment | cd-frontend.yml |
| `SENTRY_AUTH_TOKEN` | repo | release tracking |
| `SENDGRID_API_KEY` | repo | monitor.yml |
| `PAGERDUTY_TOKEN` | environment `production` | monitor.yml |
| `CODECOV_TOKEN` | repo | ci.yml |

### 13.2 GCP Secret Manager (for runtime)

Runtime secrets are pulled by Cloud Run at startup, not via GitHub.

| Secret name | Used by | Contents |
|---|---|---|
| `db-password-prod` | Cloud Run prod | PostgreSQL password |
| `db-password-dev` | Cloud Run dev | PostgreSQL password |
| `redis-auth-prod` | Cloud Run prod | Redis AUTH token |
| `redis-auth-dev` | Cloud Run dev | Redis AUTH token |
| `sentry-dsn-be-prod` | Cloud Run prod | Sentry DSN |
| `sentry-dsn-be-dev` | Cloud Run dev | Sentry DSN |
| `mlflow-token` | Cloud Run + workflows | MLflow auth |

### 13.3 Service Account

**Name**: `github-actions-sa@{project}.iam.gserviceaccount.com`

**Roles**:
- `roles/storage.admin` (manage GCS bucket)
- `roles/run.admin` (deploy Cloud Run)
- `roles/cloudsql.client` (connect to Cloud SQL)
- `roles/bigquery.dataEditor` (write to mlops dataset)
- `roles/artifactregistry.writer` (push Docker images)
- `roles/secretmanager.secretAccessor` (read runtime secrets)
- `roles/logging.logWriter` (write logs)
- `roles/monitoring.metricWriter` (custom metrics)

### 13.4 Setup Commands

```bash
# Create service account
gcloud iam service-accounts create github-actions-sa \
  --display-name "GitHub Actions SA"

# Grant roles
for ROLE in storage.admin run.admin cloudsql.client \
            bigquery.dataEditor artifactregistry.writer \
            secretmanager.secretAccessor logging.logWriter \
            monitoring.metricWriter; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member "serviceAccount:github-actions-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role "roles/$ROLE"
done

# Generate key
gcloud iam service-accounts keys create gha-key.json \
  --iam-account github-actions-sa@$PROJECT_ID.iam.gserviceaccount.com

# Add to GitHub Secrets (manually)
gh secret set GCP_SA_KEY < gha-key.json
gh secret set GCP_PROJECT_ID --body "$PROJECT_ID"

# Delete local key
rm gha-key.json
```

---

## 14. Onboarding Guide

For new team members joining mid-project.

### 14.1 Day 1: Setup

```bash
# 1. Clone repo
git clone https://github.com/your-org/mlops-project.git
cd mlops-project

# 2. Install Python environment
python3.10 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements-dev.txt

# 3. Install Node environment (frontend)
cd frontend
pnpm install
cd ..

# 4. Install tools
pip install dvc[gs] mlflow
# Install Docker Desktop separately
# Install gcloud CLI: https://cloud.google.com/sdk/docs/install
# Install Vercel CLI: npm i -g vercel

# 5. Configure git
git config user.name "Your Name"
git config user.email "you@example.com"

# 6. Authenticate gcloud
gcloud auth login
gcloud auth application-default login

# 7. Get GCP project access (ask Person 4)
gcloud config set project pso-mlops-sandy

# 8. Pull DVC data
dvc pull

# 9. Spin up local DBs
docker-compose up -d

# 10. Run training locally to verify
python ml/main.py

# 11. Run API locally
uvicorn backend.app:app --reload --port 8000

# 12. Run frontend locally
cd frontend && pnpm dev
```

### 14.2 Day 1: Read

- this document (`docs/MLOPS_PIPELINE.md`)
- `README.md`
- `docs/runbook.md`
- recent ADRs in `docs/adr/`
- existing workflow files in `.github/workflows/`

### 14.3 Day 1: Verify access

| What | How |
|---|---|
| GitHub repo write | push a branch |
| GCP project | `gcloud projects list` shows our project |
| GCS bucket | `gsutil ls gs://pso-mlops-dvc-sandy` |
| Cloud Run | `gcloud run services list --region asia-southeast1` |
| Cloud SQL | connect via Cloud SQL Proxy |
| MLflow UI | open MLflow server URL |
| Looker Studio | open dashboard URL |
| Discord channels | joined `#general`, `#alerts`, `#standup` |

### 14.4 First Week

- Pair with each owner for 1 hour to understand their pillar
- Pick 1 small ticket from backlog to ship end-to-end
- Attend Monday weekly sync
- Submit your first PR

---

## 15. Runbook and Incident Response

### 15.1 Common Incidents

#### Incident: Backend Down (Cloud Run 5xx)

**Symptom**: Sentry alert, Discord notification, dashboard shows error rate > 1%.

**Steps**:
1. Check Cloud Run logs: `gcloud run services logs read insurance-api-prod --region asia-southeast1`
2. Check recent deployments: `gcloud run revisions list --service insurance-api-prod --region asia-southeast1`
3. Rollback if recent deploy: `gcloud run services update-traffic insurance-api-prod --to-revisions={prev-rev}=100 --region asia-southeast1`
4. Verify health: `curl https://insurance-api-prod-xxx.run.app/`
5. Post-mortem in Discord `#post-mortem`

#### Incident: Database Connection Errors

**Steps**:
1. Check Cloud SQL status: `gcloud sql instances describe db-mlops-1`
2. Check connection limits: dashboard in Cloud SQL UI
3. Check Cloud Run env vars: `gcloud run services describe insurance-api-prod`
4. If proxy issue: restart Cloud Run revision
5. If Cloud SQL issue: failover to replica (if HA enabled)

#### Incident: Drift Detected (auto-handled, but verify)

**Symptom**: GitHub Issue auto-created, Discord alert, CT workflow auto-triggered.

**Steps**:
1. Open GitHub Issue, read drift report (link inside)
2. Open Evidently HTML report on GCS
3. Verify CT workflow is running: GitHub Actions tab
4. Wait for CT completion, review new model metrics in MLflow
5. If model improved, CD auto-deploys. If not, investigate root cause.

#### Incident: CI Pipeline Stuck

**Steps**:
1. Check GitHub Actions logs for failed step
2. If ephemeral (network, runner issue): re-run workflow
3. If consistent: fix code or workflow, push new commit
4. If runner outage: check https://www.githubstatus.com/

### 15.2 Rollback Procedures

| What to rollback | Command |
|---|---|
| Backend revision | `gcloud run services update-traffic insurance-api-prod --to-revisions={prev}=100` |
| Frontend deployment | `vercel rollback` |
| Database migration | `alembic downgrade -1` |
| Model in production | MLflow API: promote previous version to Production |
| Bad commit on prod | revert PR, do not force-push |

### 15.3 Escalation

| Level | Who | When |
|---|---|---|
| L1 | Discord `#alerts` | first 15 minutes |
| L2 | tag owner of the failing pillar in Discord | after 15 min no response |
| L3 | call team lead | prod down > 30 min |
| L4 | open public status page | prod down > 1 hour |

---

## 16. Glossary

| Term | Meaning |
|---|---|
| **CI** | Continuous Integration. Validate every code change before merge. |
| **CT** | Continuous Training. Auto-retrain model on schedule or trigger. |
| **CD** | Continuous Deployment. Auto-deploy code and model to environments. |
| **CM** | Continuous Monitoring. Detect data drift and runtime issues. |
| **DVC** | Data Version Control. Git-like versioning for large files. |
| **GCS** | Google Cloud Storage. Object storage on GCP. |
| **GHCR** | GitHub Container Registry. Docker image hosting. |
| **MLflow Registry** | Centralized model store with stages (None, Staging, Production, Archived). |
| **SMOTE** | Synthetic Minority Over-sampling Technique. Class imbalance fix. |
| **Pandera** | Python DataFrame schema validation library. |
| **Evidently** | Open-source data and model drift detection library. |
| **Cloud Run** | GCP serverless container platform. |
| **Cloud SQL** | GCP managed PostgreSQL / MySQL. |
| **Memorystore** | GCP managed Redis / Memcached. |
| **BigQuery** | GCP serverless analytics warehouse. |
| **Looker Studio** | Google's free dashboarding tool, formerly Data Studio. |
| **Sentry** | Error tracking SaaS. |
| **Lighthouse CI** | Automated frontend performance audit. |
| **Cosign** | Container image signing tool (Sigstore). |
| **Trivy** | CVE scanner for containers and filesystems. |
| **Alembic** | SQLAlchemy database migration framework. |
| **Canary deployment** | Deploy to a small % of traffic first, then ramp up. |
| **RACI matrix** | Responsibility assignment chart (Responsible, Accountable, Consulted, Informed). |
| **SLO** | Service Level Objective. Target reliability metric. |
| **ADR** | Architecture Decision Record. Documented design decision. |
| **WIF** | Workload Identity Federation. Keyless GCP auth from external systems. |

---

## Appendix A: Reference Architecture Diagrams

All diagrams are stored as Mermaid source in `docs/diagrams/`:

- `architecture.mmd` — full system architecture (3 swimlanes)
- `pillar-ci.mmd` — CI pipeline detail
- `pillar-ct.mmd` — CT pipeline detail
- `pillar-cd-backend.mmd` — CD Backend detail
- `pillar-cd-frontend.mmd` — CD Frontend detail
- `pillar-cm.mmd` — CM pipeline detail
- `db-schema.mmd` — database ER diagram
- `runtime-sequence.mmd` — request flow sequence

Render via https://mermaid.live or VS Code Mermaid extension.

---

## Appendix B: Useful Commands Cheat Sheet

```bash
# DVC
dvc pull                         # fetch data and model from GCS
dvc push                         # upload data and model to GCS
dvc repro                        # rerun pipeline if inputs changed
dvc status --cloud               # check sync with remote

# MLflow
mlflow ui --backend-store-uri postgres://...   # local UI to remote backend
mlflow models serve -m runs:/{run_id}/model    # local serving

# gcloud
gcloud auth login                          # human login
gcloud auth application-default login      # ADC login
gcloud config set project $PROJECT_ID      # switch project
gcloud run services list --region asia-southeast1
gcloud run services logs read insurance-api-prod --region asia-southeast1 --limit 100
gcloud sql connect db-mlops-1 --user postgres

# Docker
docker build -t local-api .
docker run -p 8000:80 local-api
docker-compose up -d              # start postgres + redis
docker-compose down -v            # tear down + remove volumes

# Vercel
vercel pull                       # pull env vars
vercel deploy                     # deploy preview
vercel deploy --prod              # deploy production
vercel rollback                   # rollback last deployment

# GitHub CLI
gh workflow run ct-train.yml      # trigger CT manually
gh workflow run cd-backend.yml -f env=prod
gh pr create --base dev           # open PR
gh secret set GCP_SA_KEY < key.json

# Alembic
alembic revision --autogenerate -m "add table"
alembic upgrade head
alembic downgrade -1
alembic history
```

---

**End of Document**

For questions or updates, open a PR against `docs/MLOPS_PIPELINE.md` and tag Person 4 as reviewer.
