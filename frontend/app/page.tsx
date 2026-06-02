import Link from "next/link";
import StatusBadge from "./_components/StatusBadge";

const FEATURES = [
  {
    icon: "⚡",
    title: "Real-time scoring",
    text: "Submit customer attributes and get an instant cross-sell prediction from the deployed model.",
  },
  {
    icon: "🔁",
    title: "Continuously trained",
    text: "The model is retrained and promoted automatically by the CT pipeline whenever data drifts.",
  },
  {
    icon: "📊",
    title: "Monitored in production",
    text: "Every prediction is logged to BigQuery and watched for drift by the monitoring pipeline.",
  },
];

export default function HomePage() {
  return (
    <main>
      <section className="hero">
        <div style={{ marginBottom: 18 }}>
          <StatusBadge />
        </div>
        <h1>Will this customer buy vehicle insurance?</h1>
        <p>
          A minimal interface over an end-to-end MLOps system — continuous
          integration, training, deployment, and monitoring — serving an
          insurance cross-sell model.
        </p>
        <Link href="/predict" className="btn btn-primary">
          Try a prediction →
        </Link>
      </section>

      <section style={{ marginTop: 48 }}>
        <p className="section-title">What's under the hood</p>
        <div className="grid cols-3">
          {FEATURES.map((f) => (
            <div className="card feature" key={f.title}>
              <div className="icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.text}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
