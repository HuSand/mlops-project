const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:80";

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

export async function postPredict(input: InputData): Promise<PredictResponse> {
  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Prediction failed (${res.status}): ${detail}`);
  }
  return res.json();
}

export { API_BASE };
