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

// The deployed model expects 10 numeric features (feature_0..feature_9).
const FIELDS: FieldDef[] = Array.from({ length: 10 }, (_, i) => ({
  name: `feature_${i}` as keyof InputData,
  label: `Feature ${i}`,
  type: "number",
  step: "any",
}));

// A non-trivial sample so the form doesn't submit all zeros.
const DEFAULTS: InputData = {
  feature_0: 0.5,
  feature_1: -0.3,
  feature_2: 1.2,
  feature_3: 0.0,
  feature_4: -1.0,
  feature_5: 0.8,
  feature_6: 0.2,
  feature_7: -0.5,
  feature_8: 1.0,
  feature_9: -0.2,
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
