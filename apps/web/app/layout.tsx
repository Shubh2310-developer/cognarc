import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "COGNARC — Tactical Skill OS",
    template: "%s | COGNARC",
  },
  description:
    "AI-powered gamified skill development. Your personal Tactical Skill OS — AI quest generation, XP tracking, and adaptive learning that never lets you decide what to study next.",
  keywords: ["skill development", "AI learning", "gamification", "coding quests", "XP system"],
  authors: [{ name: "COGNARC" }],
  openGraph: {
    type: "website",
    title: "COGNARC — Tactical Skill OS",
    description: "AI quest generation. Adaptive skill trees. Industrial-grade progress tracking.",
    siteName: "COGNARC",
  },
  robots: "index, follow",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0B0C10",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-void text-bright font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
