"use client";

import { useRef, useState, useEffect } from "react";
import { apiChat } from "@/lib/api";
import type { ChatCitation } from "@/lib/types";

type Msg = {
  role: "user" | "assistant";
  content: string;
  citations?: ChatCitation[];
  latency?: number;
};

const GREETING: Msg = {
  role: "assistant",
  content: "Hi! Ask me about your docs — I’ll answer with citations."
};

// --- helper for Copy Answer ---
async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

const LS_KEY_SHOW_TYPING = "searchsphere.showTypingBubble";

export default function Chat() {
  const [messages, setMessages] = useState<Msg[]>([GREETING]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [showTyping, setShowTyping] = useState(true);

  const ctrlRef = useRef<AbortController | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // Load persisted preference
  useEffect(() => {
    try {
      const saved = localStorage.getItem(LS_KEY_SHOW_TYPING);
      if (saved !== null) setShowTyping(saved === "1");
    } catch {}
  }, []);

  // Persist preference
  useEffect(() => {
    try {
      localStorage.setItem(LS_KEY_SHOW_TYPING, showTyping ? "1" : "0");
    } catch {}
  }, [showTyping]);

  // Auto-scroll
  useEffect(() => {
    if (chatEndRef.current) chatEndRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy, showTyping]);

  async function send() {
    const q = input.trim();
    if (!q) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: q }]);
    setBusy(true);
    try {
      if (ctrlRef.current) ctrlRef.current.abort();
      ctrlRef.current = new AbortController();
      const res = await apiChat({ query: q, k: 8 }, ctrlRef.current.signal);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.answer, citations: res.citations, latency: res.__latency_ms }
      ]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Sorry, I couldn’t answer that right now." }]);
    } finally {
      setBusy(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.key === "Enter" && (e.ctrlKey || e.metaKey)) || (e.key === "Enter" && !e.shiftKey)) {
      e.preventDefault();
      send();
    }
    // Shift+Enter inserts newline (default)
  }

  function clearChat() {
    // Optional confirm to prevent accidental clears
    const ok = window.confirm("Clear the conversation?");
    if (!ok) return;
    setMessages([GREETING]);
    setInput("");
    // Abort any in-flight request
    try { ctrlRef.current?.abort(); } catch {}
    setBusy(false);
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold">Chat (RAG)</h3>
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="badge hover:opacity-80"
            onClick={clearChat}
            disabled={busy && showTyping}
            title="Clear conversation"
          >
            Clear Chat
          </button>
          <label className="flex items-center gap-2 text-xs text-gray-600">
            <input
              type="checkbox"
              checked={showTyping}
              onChange={(e) => setShowTyping(e.target.checked)}
            />
            Show typing bubble
          </label>
          <span className="badge">{busy ? "Thinking…" : "Ready"}</span>
        </div>
      </div>

      <div className="space-y-3 max-h-[360px] overflow-auto pr-1">
        {messages.map((m, idx) => (
          <div key={idx} className={m.role === "user" ? "text-right" : ""}>
            <div
              className={
                "inline-block max-w-[90%] px-4 py-2 rounded-2xl " +
                (m.role === "user" ? "bg-brand-500 text-white" : "bg-gray-100")
              }
            >
              <div className="whitespace-pre-wrap">{m.content}</div>

              {/* --- Assistant action row --- */}
              {m.role === "assistant" && (
                <div className="mt-2 flex items-center gap-2 text-xs text-gray-600 flex-wrap">
                  <button
                    className="badge hover:opacity-80"
                    onClick={async () => {
                      const ok = await copyToClipboard(m.content);
                      if (!ok) alert("Copy failed. You can select and copy manually.");
                    }}
                  >
                    Copy answer
                  </button>

                  {m.citations && m.citations.length > 0 && (
                    <>
                      <span>•</span>
                      <span>Sources:</span>
                      {m.citations.map((c, i) => (
                        <a
                          key={i}
                          className="underline mr-1"
                          href={c.url ?? "#"}
                          target="_blank"
                          rel="noreferrer"
                        >
                          [{c.id}]
                        </a>
                      ))}
                    </>
                  )}

                  {typeof m.latency === "number" && (
                    <span className="ml-2 badge">Chat {m.latency.toFixed(0)} ms</span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator bubble */}
        {busy && showTyping && (
          <div>
            <div className="inline-block max-w-[90%] px-4 py-2 rounded-2xl bg-gray-100">
              <div className="flex items-center gap-1 h-5" aria-live="polite" aria-label="Assistant is typing">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
              </div>
            </div>
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={chatEndRef} />
      </div>

      <div className="mt-3 flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          className="input min-h-[2.5rem] max-h-32 resize-y"
          placeholder="Ask a question… (Shift+Enter for new line, Ctrl/Cmd+Enter to send)"
        />
        <button onClick={send} className="btn bg-brand-500 text-white">
          Send
        </button>
      </div>

      {/* local styles for typing indicator */}
      <style jsx>{`
        .dot {
          width: 6px;
          height: 6px;
          border-radius: 9999px;
          background: rgba(0, 0, 0, 0.45);
          display: inline-block;
          animation: blink 1.2s infinite ease-in-out;
        }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink {
          0%, 80%, 100% { opacity: 0.2; transform: translateY(0px); }
          40% { opacity: 1; transform: translateY(-2px); }
        }
      `}</style>
    </div>
  );
}
