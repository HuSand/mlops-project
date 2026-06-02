import Link from "next/link";
import { API_BASE } from "@/lib/api";

export default function HomePage() {
  return (
    <main>
      <h1>Insurance Cross-Sell Predictor</h1>
      <p>
        Minimal frontend for the MLOps prediction service. Submit customer
        features and get a cross-sell prediction from the model.
      </p>
      <p>
        <Link href="/predict">Go to the prediction form →</Link>
      </p>
      <p style={{ color: "#666", fontSize: "0.875rem" }}>
        API base URL: <code>{API_BASE}</code>
      </p>
    </main>
  );
}
