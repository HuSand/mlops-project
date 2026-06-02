"use client";

import { useState } from "react";
import Link from "next/link";
import { postPredict, type InputData, type PredictResponse } from "@/lib/api";

const DEFAULTS: InputData = {
  Gender: "Female",
  Age: 46,
  HasDrivingLicense: 1,
  RegionID: 21.0,
  Switch: 0,
  PastAccident: "Yes",
  AnnualPremium: 2305.4,
};

const NUMERIC_FIELDS: (keyof InputData)[] = [
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

  function update(field: keyof InputData, value: string) {
    setForm((prev) => ({
      ...prev,
      [field]: NUMERIC_FIELDS.includes(field) ? Number(value) : value,
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

  return (
    <main>
      <h1>Predict</h1>
      <form onSubmit={onSubmit}>
        {(Object.keys(DEFAULTS) as (keyof InputData)[]).map((field) => (
          <div key={field} style={{ marginBottom: "0.75rem" }}>
            <label style={{ display: "block", fontWeight: 600 }}>
              {field}
            </label>
            <input
              value={String(form[field])}
              onChange={(e) => update(field, e.target.value)}
              type={NUMERIC_FIELDS.includes(field) ? "number" : "text"}
              step="any"
              style={{ width: "100%", padding: "0.4rem" }}
            />
          </div>
        ))}
        <button type="submit" disabled={loading} style={{ padding: "0.5rem 1rem" }}>
          {loading ? "Predicting…" : "Predict"}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: "1.5rem" }}>
          <h2>Result</h2>
          <p>
            Predicted class: <strong>{result.predicted_class}</strong>
          </p>
          <p>Model version: {result.model_version}</p>
        </div>
      )}

      {error && (
        <p style={{ color: "crimson", marginTop: "1.5rem" }}>Error: {error}</p>
      )}

      <p style={{ marginTop: "2rem" }}>
        <Link href="/">← Back</Link>
      </p>
    </main>
  );
}
