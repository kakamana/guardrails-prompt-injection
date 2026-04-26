import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Prompt Guard",
  description: "Guardrails & Prompt Injection Defense",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
