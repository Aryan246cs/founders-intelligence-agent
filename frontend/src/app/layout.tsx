import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Founder Intelligence Agent",
  description: "Autonomous multi-agent platform for startup founders",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-950 text-gray-100 min-h-screen`}>
        <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-4">
          <span className="font-semibold text-brand-500 text-lg">Founder Intelligence</span>
          <a href="/" className="text-sm text-gray-400 hover:text-white">Dashboard</a>
          <a href="/research" className="text-sm text-gray-400 hover:text-white">Research</a>
          <a href="/briefings" className="text-sm text-gray-400 hover:text-white">Briefings</a>
          <a href="/memory" className="text-sm text-gray-400 hover:text-white">Memory</a>
        </nav>
        <main className="max-w-6xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
