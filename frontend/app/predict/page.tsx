"use client";

import { useState } from "react";
import Link from "next/link";
import { postPredict, type InputData, type PredictResponse } from "@/lib/api";

interface FieldDef {
  name: keyof InputData;
  label: string;
  hint?: string;
  type: "number" | "select";
  step?: string;
  options?: { label: string; value: string | number }[];
}

const FIELDS: FieldDef[] = [
  {
    name: "Gender",
    label: "Gender",
    type: "select",
    options: [
      { label: "Female", value: "Female" },
      { label: "Male", value: "Male" },
    ],
  },
  { name: "Age", label: "Age", type: "number", step: "1", hint: "years" },
  {
    name: "HasDrivingLicense",
    label: "Driving license",
    type: "select",
    options: [
      { label: "Yes", value: 1 },
      { label: "No", value: 0 },
    ],
  },
  { name: "RegionID", label: "Region ID", type: "number", step: "1" },
  {
    name: "Switch",
    label: "Previously switched",
    type: "select",
    options: [
      { label: "No", value: 0 },
      { label: "Yes", value: 1 },
      { label: "Unknown", value: -1 },
    ],
  },
  {
    name: "PastAccident",
    label: "Past accident",
    type: "select",
    options: [
      { label: "No", value: "No" },
      { label: "Yes", value: "Yes" },
      { label: "Unknown", value: "Unknown" },
    ],
  },
  {
    name: "AnnualPremium",
    label: "Annual premium",
    type: "number",
    step: "any",
    hint: "currency amount",
  },
];

const DEFAULTS: InputData = {
  Gender: "Female",
  Age: 46,
  HasDrivingLicense: 1,
  RegionID: 21,
  Switch: 0,
  PastAccident: "Yes",
  AnnualPremium: 2305.4,
};

// Fields whose value must be coerced to a number on input.
const NUMERIC: (keyof InputData)[] = [
  "Age",
  "HasDrivingLicense",
  "RegionID",
  "Switch",
  "AnnualPremium",
];

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
                {f.label} {f.hint && <span className="hint">({f.hint})</span>}
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
