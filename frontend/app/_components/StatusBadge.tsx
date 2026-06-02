"use client";

import { useEffect, useState } from "react";
import { getHealth, API_BASE, type HealthResponse } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthResponse }
  | { kind: "error"; message: string };

export default function StatusBadge() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    getHealth()
      .then((data) => active && setState({ kind: "ok", data }))
      .catch(
        (e) =>
          active &&
          setState({ kind: "error", message: e?.message ?? "unreachable" })
      );
    return () => {
      active = false;
    };
  }, []);

  if (state.kind === "loading") {
    return (
      <span className="status">
        <span className="dot amber" /> Checking API…
      </span>
    );
  }

  if (state.kind === "error") {
    return (
      <span className="status" title={state.message}>
        <span className="dot red" /> API offline
      </span>
    );
  }

  const { model_loaded, env, model_version } = state.data;
  return (
    <span className="status" title={`API base: ${API_BASE}`}>
      <span className={`dot ${model_loaded ? "green" : "amber"}`} />
      API online · {model_loaded ? "model loaded" : "no model"} ·{" "}
      <span className="muted">
        {env} · v{model_version}
      </span>
    </span>
  );
}
