const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://insurance-api-dev-6n767ucvla-et.a.run.app";

export interface InputData {
  feature_0: number;
  feature_1: number;
  feature_2: number;
  feature_3: number;
  feature_4: number;
  feature_5: number;
  feature_6: number;
  feature_7: number;
  feature_8: number;
  feature_9: number;
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

export interface MonitoringResponse {
  status: "success" | "error";
  message?: string;
  data?: {
    execution_date: string;
    timestamp: string;
    summary: {
      drift_detected: boolean;
      drift_share: number;
      number_of_columns: number;
      drifted_columns_count: number;
    };
    drift_details: { feature: string; drift_score: number }[];
    data_health: {
      missing_values_count: number;
      total_predictions: number;
    };
    report_url: string;
  };
}

export async function getMonitoring(): Promise<MonitoringResponse> {
  const res = await fetch(`${API_BASE}/api/v1/monitoring/latest`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Monitoring fetch failed (${res.status})`);
  }
  return res.json();
}

export interface BusinessInsights {
  status: "success" | "error";
  message?: string;
  data?: {
    kpis: {
      total_scored: number;
      interest_rate: number;
      avg_premium: number;
      interested_leads: number;
      avg_premium_interested: number;
    };
    by_gender: { gender: string; n: number; interest_pct: number; avg_premium: number }[];
    by_age_band: { band: string; n: number; interest_pct: number }[];
    by_premium_band: { band: string; n: number; interest_pct: number }[];
    by_past_accident: { value: string; n: number; interest_pct: number }[];
    trend: { date: string; total: number; interested: number; interest_pct: number }[];
  };
}

export async function getBusinessInsights(): Promise<BusinessInsights> {
  const res = await fetch(`${API_BASE}/api/v1/insights/business`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Insights fetch failed (${res.status})`);
  }
  return res.json();
}

export interface MonitoringOps {
  status: "success" | "error";
  message?: string;
  data?: {
    total_predictions: number;
    last_prediction_ts: string | null;
    volume_by_day: { date: string; n: number }[];
    by_model_version: { model_version: string; n: number }[];
  };
}

export async function getMonitoringOps(): Promise<MonitoringOps> {
  const res = await fetch(`${API_BASE}/api/v1/monitoring/ops`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Ops fetch failed (${res.status})`);
  }
  return res.json();
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
