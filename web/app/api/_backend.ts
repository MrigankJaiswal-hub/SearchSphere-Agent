// web/app/api/_backend.ts
export function normalizeBase(v?: string) {
  if (!v) return "";
  let s = v.trim();
  if (s.endsWith("/")) s = s.slice(0, -1);
  if (s.toLowerCase().endsWith("/api")) s = s.slice(0, -4);
  return s;
}

/**
 * Prefer NEXT_PUBLIC_API_BASE in prod builds (direct to backend),
 * else use BACKEND_URL (server env), else localhost for dev.
 */
export function getBackendBase() {
  const pub = normalizeBase(process.env.NEXT_PUBLIC_API_BASE);
  if (pub) return pub;

  const srv = normalizeBase(
    process.env.BACKEND_URL ||
      process.env.NEXT_PUBLIC_BACKEND_URL ||
      process.env.BACKEND_API_BASE
  );
  return srv || "http://127.0.0.1:8080";
}
