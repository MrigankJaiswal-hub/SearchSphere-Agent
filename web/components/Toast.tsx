// components/Toast.tsx
"use client";

import { AnimatePresence, motion } from "framer-motion";

export default function Toast({
  show,
  message,
  onClose,
  duration = 2200,
}: {
  show: boolean;
  message: string;
  onClose: () => void;
  duration?: number;
}) {
  // auto close
  if (show) {
    // very small guard to avoid setting timers during SSR
    if (typeof window !== "undefined") {
      window.clearTimeout((Toast as any)._t);
      (Toast as any)._t = window.setTimeout(onClose, duration);
    }
  }

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -20, opacity: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 22 }}
          className="fixed top-4 left-1/2 -translate-x-1/2 z-50"
        >
          <div className="rounded-xl border border-gray-200 bg-white/85 backdrop-blur px-4 py-2 shadow-lg flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
            <span className="text-sm text-gray-800">{message}</span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
