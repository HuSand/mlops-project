import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Insurance Cross-Sell Predictor",
  description:
    "Predict whether a customer is likely to buy vehicle insurance — powered by an MLOps pipeline.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <div className="container inner">
            <Link href="/" className="brand">
              <span className="logo">🛡️</span>
              <span>CrossSell&nbsp;AI</span>
            </Link>
            <nav className="nav">
              <Link href="/">Home</Link>
              <Link href="/predict">Predict</Link>
              <Link href="/insights">Insights</Link>
              <Link href="/monitoring">Monitoring</Link>
            </nav>
          </div>
        </header>

        <div className="container">{children}</div>

        <footer className="footer">
          <div className="container">
            Insurance Cross-Sell Predictor · MLOps demo (CI · CT · CD · CM)
          </div>
        </footer>
      </body>
    </html>
  );
}
