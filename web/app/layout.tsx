import "./globals.css";
import Image from "next/image";
import { ReactNode } from "react";

export const metadata = {
  title: "SearchSphere Agent",
  description: "Elastic + Vertex AI hybrid RAG assistant",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  const buildSha = process.env.NEXT_PUBLIC_BUILD_SHA || "dev";

  return (
    <html lang="en">
      <body className="min-h-screen">
        {/* Fixed background layer */}
        <div
          className="fixed inset-0 -z-10 opacity-35"
          style={{
            backgroundImage: "url('/bg-pattern.svg')",
            backgroundRepeat: "repeat",
            backgroundSize: "600px auto",
          }}
          aria-hidden="true"
        />

        <div className="min-h-screen flex flex-col">
          {/* Top nav */}
          <nav className="border-b bg-white/90 backdrop-blur supports-[backdrop-filter]:bg-white/70">
            <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
              {/* left: logo + title */}
              <div className="flex items-center gap-3 min-w-0">
                {/* If your file is /public/logo.svg */}
                <Image
                  src="/logo.png"
                  alt="SearchSphere Agent"
                  width={32}
                  height={32}
                  priority
                />
                <span className="font-semibold text-lg truncate">
                  SearchSphere Agent
                </span>
                <span className="text-xs text-gray-400 ml-2 shrink-0">
                  build: {buildSha}
                </span>
              </div>

              {/* right: helper links */}
              <div className="text-sm text-gray-600 flex items-center gap-4">
                <span className="hidden sm:inline">
                  Elastic + Google Cloud (Vertex AI)
                </span>
                <a className="underline" href="/label">Label Assist</a>
              </div>
            </div>
          </nav>

          {/* Main content area */}
          <main className="flex-1">{children}</main>

          {/* Footer */}
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
