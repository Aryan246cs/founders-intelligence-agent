import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  // A tab title is read at a glance in a crowded tab strip, so the product
  // name leads and the page name follows.
  title: {
    default: "Founder Intel",
    template: "%s · Founder Intel",
  },
  description:
    "Competitive intelligence for founders — autonomous competitor research, pricing analysis and executive briefings.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans bg-zinc-950 text-zinc-100 min-h-screen`}>
        <Sidebar />
        <Topbar />
        <main className="ml-60 pt-14 min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}
