const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://insurance-api-dev-6n767ucvla-et.a.run.app";

export interface InputData {
  Gender: string;
  Age: number;
  HasDrivingLicense: number;
  RegionID: number;
  Switch: number;
  PastAccident: string;
  AnnualPremium: number;
}

export interface PredictResponse {
  predicted_class: number;
  model_version: string;
}

export interface HealthResponse {
  health_check: string;
  model_version: string;
  env: string;
  model_loaded: boolean;
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Health check failed (${res.status})`);
  }
  return res.json();
}

export async function postPredict(input: InputData): Promise<PredictResponse> {
  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    let detail = await res.text();
    try {
      detail = JSON.parse(detail).detail ?? detail;
    } catch {
      /* keep raw text */
    }
    throw new Error(`Prediction failed (${res.status}): ${detail}`);
  }
  return res.json();
}

export { API_BASE };
