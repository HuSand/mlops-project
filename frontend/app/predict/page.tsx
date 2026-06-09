"use client";

import { useState } from "react";
import Link from "next/link";
import { postPredict, type InputData, type PredictResponse } from "@/lib/api";

// Human-friendly form. The deployed model takes 10 numeric features
// (feature_0..feature_9); we expose the 7 that map to insurance attributes and
// send feature_7..9 as fixed defaults (they carry no business meaning).
interface HumanForm {
  gender: number;
  age: number;
  license: number;
  region: number;
  switched: number;
  accident: number;
  premium: number;
}

interface FieldDef {
  name: keyof HumanForm;
  label: string;
  hint?: string;
  type: "number" | "select";
  step?: string;
  options?: { label: string; value: number }[];
}

const FIELDS: FieldDef[] = [
  {
    name: "gender",
    label: "Gender",
    type: "select",
    options: [
      { label: "Female", value: 0 },
      { label: "Male", value: 1 },
    ],
  },
  { name: "age", label: "Age", type: "number", step: "1", hint: "years" },
  {
    name: "license",
    label: "Driving license",
    type: "select",
    options: [
      { label: "Yes", value: 1 },
      { label: "No", value: 0 },
    ],
  },
  { name: "region", label: "Region ID", type: "number", step: "1" },
  {
    name: "switched",
    label: "Previously switched",
    type: "select",
    options: [
      { label: "No", value: 0 },
      { label: "Yes", value: 1 },
      { label: "Unknown", value: -1 },
    ],
  },
  {
    name: "accident",
    label: "Past accident",
    type: "select",
    options: [
      { label: "No", value: 0 },
      { label: "Yes", value: 1 },
      { label: "Unknown", value: 2 },
    ],
  },
  {
    name: "premium",
    label: "Annual premium",
    type: "number",
    step: "any",
    hint: "currency amount",
  },
];

const DEFAULTS: HumanForm = {
  gender: 0,
  age: 35,
  license: 1,
  region: 12,
  switched: 0,
  accident: 0,
  premium: 25000,
};

/** Map the human form to the model's feature_0..feature_9 contract. */
function toModelInput(f: HumanForm): InputData {
  return {
    feature_0: f.gender,
    feature_1: f.age,
    feature_2: f.license,
    feature_3: f.region,
    feature_4: f.switched,
    feature_5: f.accident,
    feature_6: f.premium,
    feature_7: 0,
    feature_8: 0,
    feature_9: 0,
  };
}

export default function PredictPage() {
  const [form, setForm] = useState<HumanForm>(DEFAULTS);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function update(name: keyof HumanForm, raw: string) {
    setForm((prev) => ({ ...prev, [name]: Number(raw) }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await postPredict(toModelInput(form)));
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
                {f.hint && <span className="hint">({f.hint})</span>}
              </label>
              {f.type === "select" ? (
                <select
                  id={f.name}
                  value={String(form[f.name])}
                  onChange={(e) => update(f.name, e.target.value)}
                >
                  {f.options!.map((o) => (
                    <option key={o.value} value={String(o.value)}>
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
