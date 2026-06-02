import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Insurance Cross-Sell Predictor",
  description: "Minimal UI for the MLOps prediction service",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body
        style={{
          fontFamily: "system-ui, sans-serif",
          maxWidth: 640,
          margin: "0 auto",
          padding: "2rem 1rem",
        }}
      >
        {children}
      </body>
    </html>
  );
}
