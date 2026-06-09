"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export const COLORS = {
  accent: "#6366f1",
  accent2: "#8b5cf6",
  green: "#22c55e",
  red: "#ef4444",
  amber: "#f59e0b",
  muted: "#9aa7c2",
  border: "#263254",
};

const PALETTE = [COLORS.accent, COLORS.accent2, COLORS.green, COLORS.amber, COLORS.red];

const tooltipStyle = {
  background: "#161f38",
  border: `1px solid ${COLORS.border}`,
  borderRadius: 10,
  color: "#e8edf7",
  fontSize: 13,
};

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card">
      <p className="section-title" style={{ margin: "0 0 4px" }}>
        {title}
      </p>
      {subtitle && (
        <p className="muted" style={{ margin: "0 0 12px", fontSize: 13 }}>
          {subtitle}
        </p>
      )}
      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          {children as React.ReactElement}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

type Datum = Record<string, string | number>;

export function BarCard({
  title,
  subtitle,
  data,
  xKey,
  yKey,
  colorByIndex = false,
  unit = "",
}: {
  title: string;
  subtitle?: string;
  data: Datum[];
  xKey: string;
  yKey: string;
  colorByIndex?: boolean;
  unit?: string;
}) {
  return (
    <ChartCard title={title} subtitle={subtitle}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
        <XAxis dataKey={xKey} tick={{ fill: COLORS.muted, fontSize: 12 }} />
        <YAxis tick={{ fill: COLORS.muted, fontSize: 12 }} />
        <Tooltip
          contentStyle={tooltipStyle}
          cursor={{ fill: "rgba(99,102,241,0.08)" }}
          formatter={(v: number | string) => `${v}${unit}`}
        />
        <Bar dataKey={yKey} radius={[6, 6, 0, 0]} fill={COLORS.accent}>
          {colorByIndex &&
            data.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
        </Bar>
      </BarChart>
    </ChartCard>
  );
}

export function LineCard({
  title,
  subtitle,
  data,
  xKey,
  lines,
}: {
  title: string;
  subtitle?: string;
  data: Datum[];
  xKey: string;
  lines: { key: string; name: string; color: string }[];
}) {
  return (
    <ChartCard title={title} subtitle={subtitle}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
        <XAxis dataKey={xKey} tick={{ fill: COLORS.muted, fontSize: 12 }} />
        <YAxis tick={{ fill: COLORS.muted, fontSize: 12 }} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ stroke: COLORS.border }} />
        {lines.map((l) => (
          <Line
            key={l.key}
            type="monotone"
            dataKey={l.key}
            name={l.name}
            stroke={l.color}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ChartCard>
  );
}
