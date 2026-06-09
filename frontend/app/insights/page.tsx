"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { getBusinessInsights, type BusinessInsights } from "@/lib/api";
import { BarCard, COLORS, LineCard } from "../_components/Charts";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: BusinessInsights }
  | { kind: "error"; message: string };

function Kpi({ label, value, sub }: { label: string; value: string; sub?: string }) {
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

export default function InsightsPage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  const load = useCallback(() => {
    setState({ kind: "loading" });
    getBusinessInsights()
      .then((data) => setState({ kind: "ok", data }))
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
          <h1 style={{ margin: "0 0 6px", fontSize: 28 }}>Business insights</h1>
          <p className="muted" style={{ margin: 0 }}>
            Cross-sell opportunity across the scored customer base — for management & marketing.
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
            <span className="dot amber" /> Loading insights…
          </span>
        </div>
      )}

      {state.kind === "error" && (
        <div className="alert">⚠️ Could not load insights: {state.message}</div>
      )}

      {state.kind === "ok" && state.data.status !== "success" && (
        <div className="alert">⚠️ {state.data.message ?? "No insight data available yet."}</div>
      )}

      {state.kind === "ok" && state.data.status === "success" && state.data.data && (
        <InsightsBody data={state.data.data} />
      )}

      <p style={{ marginTop: 22 }}>
        <Link href="/" className="muted">
          ← Back to home
        </Link>
      </p>
    </main>
  );
}

function InsightsBody({ data }: { data: NonNullable<BusinessInsights["data"]> }) {
  const { kpis } = data;
  const currency = (n: number) =>
    n.toLocaleString(undefined, { maximumFractionDigits: 0 });

  return (
    <>
      <div className="grid cols-3">
        <Kpi
          label="Customers scored"
          value={kpis.total_scored.toLocaleString()}
          sub="total predictions logged"
        />
        <Kpi
          label="Cross-sell opportunity"
          value={`${kpis.interest_rate}%`}
          sub={`${kpis.interested_leads.toLocaleString()} interested leads`}
        />
        <Kpi
          label="Avg annual premium"
          value={currency(kpis.avg_premium)}
          sub={`interested: ${currency(kpis.avg_premium_interested)}`}
        />
      </div>

      <div style={{ marginTop: 16 }}>
        <LineCard
          title="Interest trend"
          subtitle="Predicted-interest rate per day (%)"
          data={data.trend}
          xKey="date"
          lines={[{ key: "interest_pct", name: "Interest %", color: COLORS.accent }]}
        />
      </div>

      <div className="grid cols-2" style={{ marginTop: 16 }}>
        <BarCard
          title="Interest by gender"
          subtitle="% predicted interested"
          data={data.by_gender}
          xKey="gender"
          yKey="interest_pct"
          colorByIndex
          unit="%"
        />
        <BarCard
          title="Interest by age band"
          subtitle="% predicted interested"
          data={data.by_age_band}
          xKey="band"
          yKey="interest_pct"
          unit="%"
        />
      </div>

      <div className="grid cols-2" style={{ marginTop: 16 }}>
        <BarCard
          title="Interest by premium band"
          subtitle="% predicted interested"
          data={data.by_premium_band}
          xKey="band"
          yKey="interest_pct"
          unit="%"
        />
        <BarCard
          title="Interest by past accident"
          subtitle="% predicted interested"
          data={data.by_past_accident}
          xKey="value"
          yKey="interest_pct"
          colorByIndex
          unit="%"
        />
      </div>
    </>
  );
}
