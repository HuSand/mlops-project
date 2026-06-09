"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  getABComparison,
  getMonitoring,
  getMonitoringOps,
  type ABComparison,
  type MonitoringOps,
  type MonitoringResponse,
} from "@/lib/api";
import { BarCard, COLORS, LineCard } from "../_components/Charts";

type State =
  | { kind: "loading" }
  | { kind: "ok"; drift: MonitoringResponse; ops: MonitoringOps; ab: ABComparison }
  | { kind: "error"; message: string };

function Metric({
  label,
  value,
  sub,
}: {
  label: string;
  value: React.ReactNode;
  sub?: string;
}) {
  return (
    <div className="card">
      <p className="section-title" style={{ margin: "0 0 8px" }}>
        {label}
      </p>
      <p style={{ fontSize: 26, fontWeight: 700, margin: 0 }}>{value}</p>
      {sub && (
        <p className="muted" style={{ margin: "4px 0 0", fontSize: 13 }}>
          {sub}
        </p>
      )}
    </div>
  );
}

export default function MonitoringPage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  const load = useCallback(() => {
    setState({ kind: "loading" });
    Promise.all([getMonitoring(), getMonitoringOps(), getABComparison()])
      .then(([drift, ops, ab]) => setState({ kind: "ok", drift, ops, ab }))
      .catch((e) => setState({ kind: "error", message: e?.message ?? "unreachable" }));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <main>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 16,
          marginBottom: 24,
        }}
      >
        <div>
          <h1 style={{ margin: "0 0 6px", fontSize: 28 }}>Monitoring &amp; performance</h1>
          <p className="muted" style={{ margin: 0 }}>
            Data drift and operational health of the production model.
          </p>
        </div>
        <button
          type="button"
          className="btn btn-ghost"
          onClick={load}
          disabled={state.kind === "loading"}
        >
          {state.kind === "loading" ? "Refreshing…" : "↻ Refresh"}
        </button>
      </div>

      {state.kind === "loading" && (
        <div className="card">
          <span className="status">
            <span className="dot amber" /> Loading monitoring data…
          </span>
        </div>
      )}

      {state.kind === "error" && (
        <div className="alert">⚠️ Could not load monitoring data: {state.message}</div>
      )}

      {state.kind === "ok" && (
        <>
          <ABSection ab={state.ab} />
          <OpsSection ops={state.ops} />
          <DriftSection drift={state.drift} />
        </>
      )}

      <p style={{ marginTop: 22 }}>
        <Link href="/" className="muted">
          ← Back to home
        </Link>
      </p>
    </main>
  );
}

function ABSection({ ab }: { ab: ABComparison }) {
  if (ab.status !== "success" || !ab.data || ab.data.versions.length === 0) {
    return null; // A/B panel is optional; stay quiet when there's no data
  }
  const { versions, comparison, window_hours, total_predictions } = ab.data;
  const chartData = versions.map((v) => ({
    model_version: v.model_version,
    traffic_pct: v.traffic_pct,
    positive_rate: v.positive_rate,
  }));
  // Chronological performance: one point per model version (each training run),
  // ordered by when it first appeared.
  const timeline = [...versions]
    .filter((v) => v.first_seen)
    .sort((a, b) => (a.first_seen! < b.first_seen! ? -1 : 1))
    .map((v) => ({
      model_version: v.model_version,
      positive_rate: v.positive_rate,
      predictions: v.n,
    }));

  return (
    <>
      <p className="section-title">Model A/B (champion vs challenger)</p>
      <div style={{ marginBottom: 16 }}>
        {comparison ? (
          <span className="status">
            <span className="dot green" /> champion <b>&nbsp;{comparison.champion}</b>
            &nbsp;vs challenger <b>&nbsp;{comparison.challenger}</b> · pos-rate Δ{" "}
            <span className="mono">
              {comparison.positive_rate_delta > 0 ? "+" : ""}
              {comparison.positive_rate_delta}%
            </span>
          </span>
        ) : (
          <span className="status">
            <span className="dot amber" /> single version (no challenger traffic yet)
          </span>
        )}
      </div>
      <div className="grid cols-2">
        <BarCard
          title="Traffic share"
          subtitle={`last ${window_hours}h · ${total_predictions} predictions`}
          data={chartData}
          xKey="model_version"
          yKey="traffic_pct"
          colorByIndex
          unit="%"
        />
        <BarCard
          title="Positive-prediction rate"
          subtitle="% predicted class 1 per version"
          data={chartData}
          xKey="model_version"
          yKey="positive_rate"
          colorByIndex
          unit="%"
        />
      </div>
      <div style={{ marginTop: 16 }}>
        <LineCard
          title="Model performance over time"
          subtitle="positive-prediction rate per model version (each training, oldest → newest)"
          data={timeline}
          xKey="model_version"
          lines={[
            { key: "positive_rate", name: "Positive %", color: COLORS.accent2 },
          ]}
        />
      </div>
    </>
  );
}

function OpsSection({ ops }: { ops: MonitoringOps }) {
  if (ops.status !== "success" || !ops.data) {
    return (
      <div className="alert">⚠️ {ops.message ?? "No operational data available yet."}</div>
    );
  }
  const { total_predictions, last_prediction_ts, volume_by_day, by_model_version } = ops.data;
  return (
    <>
      <p className="section-title">Operational</p>
      <div className="grid cols-2">
        <Metric
          label="Total predictions"
          value={total_predictions.toLocaleString()}
          sub="served by the API"
        />
        <Metric
          label="Last prediction"
          value={
            last_prediction_ts
              ? new Date(last_prediction_ts).toLocaleString()
              : "—"
          }
          sub="most recent request"
        />
      </div>
      <div className="grid cols-2" style={{ marginTop: 16 }}>
        <LineCard
          title="Prediction volume"
          subtitle="Requests per day"
          data={volume_by_day}
          xKey="date"
          lines={[{ key: "n", name: "Predictions", color: COLORS.accent }]}
        />
        <BarCard
          title="By model version"
          subtitle="Predictions served per version"
          data={by_model_version}
          xKey="model_version"
          yKey="n"
          colorByIndex
        />
      </div>
    </>
  );
}

function DriftSection({ drift }: { drift: MonitoringResponse }) {
  if (drift.status !== "success" || !drift.data) {
    return (
      <div className="alert" style={{ marginTop: 24 }}>
        ⚠️ {drift.message ?? "No drift report available yet (monitor pipeline pending)."}
      </div>
    );
  }
  const d = drift.data;
  const isDrift = d.summary.drift_detected;
  return (
    <>
      <p className="section-title" style={{ marginTop: 28 }}>
        Data drift
      </p>
      <div style={{ marginBottom: 16 }}>
        <span className="status" title={d.timestamp}>
          <span className={`dot ${isDrift ? "red" : "green"}`} />
          {isDrift ? "Drift detected" : "Model healthy"} ·{" "}
          <span className="muted">as of {d.execution_date}</span>
        </span>
      </div>

      <div className="grid cols-3">
        <Metric
          label="Drift status"
          value={isDrift ? "⚠️ Drift" : "✅ Healthy"}
          sub={`share ${d.summary.drift_share.toFixed(3)}`}
        />
        <Metric
          label="Drifted columns"
          value={`${d.summary.drifted_columns_count} / ${d.summary.number_of_columns}`}
          sub="columns flagged"
        />
        <Metric
          label="Missing values"
          value={d.data_health.missing_values_count.toLocaleString()}
          sub="in current window"
        />
      </div>

      {d.drift_details.length > 0 && (
        <div className="card" style={{ marginTop: 16 }}>
          <p className="section-title" style={{ margin: "0 0 10px" }}>
            Drifted features
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {d.drift_details.map((f) => (
              <span
                key={f.feature}
                className="status"
                title={`drift score: ${f.drift_score.toFixed(3)}`}
              >
                <span className="dot red" /> {f.feature}
                <span className="muted mono">&nbsp;{f.drift_score.toFixed(2)}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="card" style={{ marginTop: 16 }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 12,
          }}
        >
          <p className="section-title" style={{ margin: 0 }}>
            Full drift report
          </p>
          <a href={d.report_url} target="_blank" rel="noopener noreferrer" className="muted">
            Open in new tab ↗
          </a>
        </div>
        <iframe
          src={d.report_url}
          title="Evidently drift report"
          style={{
            width: "100%",
            height: 640,
            border: `1px solid ${COLORS.border}`,
            borderRadius: 10,
            background: "#fff",
          }}
        />
      </div>
    </>
  );
}
