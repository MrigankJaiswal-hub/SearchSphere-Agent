import "./globals.css";
import { ReactNode } from "react";
import Header from "@/components/Header";

export const metadata = {
  title: "SearchSphere Agent",
  description: "Elastic + Vertex AI hybrid RAG assistant",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        {/* Background pattern layer (single SVG in /public) */}
        <div
          className="fixed inset-0 -z-10 opacity-35 bg-pattern-animate"
          style={{
            backgroundImage: "url('/bg-pattern.svg')",
            backgroundRepeat: "repeat",
            backgroundSize: "600px auto",
          }}
          aria-hidden="true"
        />

        {/* App chrome */}
        <div className="min-h-screen flex flex-col">
          <Header />

          <main className="flex-1">{children}</main>

          <footer className="border-t bg-white/80">
            <div className="mx-auto max-w-6xl px-4 py-3 text-xs text-gray-600">
              © {new Date().getFullYear()} SearchSphere • Demo build for AI Accelerate Hackathon
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
