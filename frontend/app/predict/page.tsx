"use client";

import { useState } from "react";
import Link from "next/link";
import { postPredict, type InputData, type PredictResponse } from "@/lib/api";

type Option = { label: string; value: string | number };

interface FieldDef {
  name: keyof InputData;
  label: string;
  hint?: string;
  type: "number" | "select";
  step?: string;
  options?: Option[];
}

const FIELDS: FieldDef[] = [
  {
    name: "feature_0",
    label: "Gender",
    hint: "Display only; value is sent as feature_0",
    type: "number",
    step: "any",
  },
  {
    name: "feature_1",
    label: "Age",
    hint: "Customer age in years",
    type: "number",
    step: "1",
  },
  {
    name: "feature_2",
    label: "Has Driving License",
    hint: "Display only; value is sent as feature_2",
    type: "number",
    step: "any",
  },
  {
    name: "feature_3",
    label: "Region",
    hint: "Customer region code",
    type: "number",
    step: "1",
  },
  {
    name: "feature_4",
    label: "Switch",
    hint: "Display only; value is sent as feature_4",
    type: "number",
    step: "any",
  },
  {
    name: "feature_5",
    label: "Past Accident",
    hint: "Display only; value is sent as feature_5",
    type: "number",
    step: "any",
  },
  {
    name: "feature_6",
    label: "Annual Premium",
    hint: "Annual premium amount",
    type: "number",
    step: "any",
  },
  {
    name: "feature_7",
    label: "Feature 7",
    hint: "One of the internal model features",
    type: "number",
    step: "any",
  },
  {
    name: "feature_8",
    label: "Feature 8",
    hint: "One of the internal model features",
    type: "number",
    step: "any",
  },
  {
    name: "feature_9",
    label: "Feature 9",
    hint: "One of the internal model features",
    type: "number",
    step: "any",
  },
];

// A non-trivial sample so the form doesn't submit all zeros.
const DEFAULTS: InputData = {
  feature_0: 1,
  feature_1: 35,
  feature_2: 1,
  feature_3: 12,
  feature_4: 0,
  feature_5: 0,
  feature_6: 25000,
  feature_7: 0.1,
  feature_8: -0.2,
  feature_9: 0.3,
};

const NUMERIC: (keyof InputData)[] = FIELDS.map((f) => f.name);

export default function PredictPage() {
  const [form, setForm] = useState<InputData>(DEFAULTS);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function update(name: keyof InputData, raw: string) {
    setForm((prev) => ({
      ...prev,
      [name]: NUMERIC.includes(name) ? Number(raw) : raw,
    }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await postPredict(form));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setForm(DEFAULTS);
    setResult(null);
    setError(null);
  }

  const willBuy = result?.predicted_class === 1;

  return (
    <main>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: "0 0 6px", fontSize: 28 }}>Make a prediction</h1>
        <p className="muted" style={{ margin: 0 }}>
          Fill in the customer attributes and the model will estimate whether
          they are likely to buy vehicle insurance.
        </p>
        <p className="muted" style={{ margin: "8px 0 0", fontSize: 14 }}>
          Labels ditampilkan lebih ramah di frontend; nilai tetap dikirim ke
          backend sebagai feature_0..feature_9.
        </p>
      </div>

      <form className="card" onSubmit={onSubmit}>
        <div className="form-grid">
          {FIELDS.map((f) => (
            <div className="field" key={f.name}>
              <label htmlFor={f.name}>
                {f.label}{" "}
                {f.hint && <span className="hint">{f.hint}</span>}
              </label>
              {f.type === "select" ? (
                <select
                  id={f.name}
                  value={String(form[f.name])}
                  onChange={(e) => update(f.name, e.target.value)}
                >
                  {f.options!.map((o) => (
                    <option key={String(o.value)} value={String(o.value)}>
                      {o.label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  id={f.name}
                  type="number"
                  step={f.step}
                  value={String(form[f.name])}
                  onChange={(e) => update(f.name, e.target.value)}
                />
              )}
            </div>
          ))}
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Predicting…" : "Predict"}
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={reset}
            disabled={loading}
          >
            Reset
          </button>
        </div>

        {result && (
          <div className={`result ${willBuy ? "positive" : "negative"}`}>
            <p className="muted" style={{ margin: 0 }}>
              Prediction
            </p>
            <p className="big">
              {willBuy
                ? "✅ Likely to buy insurance"
                : "➖ Unlikely to buy insurance"}
            </p>
            <p className="muted mono" style={{ margin: 0 }}>
              class={result.predicted_class} · model v{result.model_version}
            </p>
          </div>
        )}

        {error && <div className="alert">⚠️ {error}</div>}
      </form>

      <p style={{ marginTop: 22 }}>
        <Link href="/" className="muted">
          ← Back to home
        </Link>
      </p>
    </main>
  );
}
