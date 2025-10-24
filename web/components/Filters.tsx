"use client";

import { motion, type Variants } from "framer-motion";

type Props = {
  team: string[];
  setTeam: (val: string[]) => void;
  docType: string[];
  setDocType: (val: string[]) => void;
  since?: string;
  setSince: (val?: string) => void;
};

const container: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06 },
  },
};

// use cubic-bezier array for type-safe easing
const row: Variants = {
  hidden: { opacity: 0, y: 8 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.25, ease: [0.16, 1, 0.3, 1] },
  },
};

export default function Filters({
  team,
  setTeam,
  docType,
  setDocType,
  since,
  setSince,
}: Props) {
  return (
    <motion.div
      initial="hidden"
      animate="show"
      variants={container}
      className="space-y-3"
      aria-label="Search filters"
    >
      <motion.div variants={row}>
        <label className="text-sm font-medium" htmlFor="team-input">
          Team
        </label>
        <input
          id="team-input"
          className="input"
          placeholder="e.g., AI Research"
          value={team.join(", ")}
          onChange={(e) =>
            setTeam(
              e.currentTarget.value
                .split(",")
                .map((t) => t.trim())
                .filter(Boolean)
            )
          }
        />
      </motion.div>

      <motion.div variants={row}>
        <label className="text-sm font-medium" htmlFor="doctype-input">
          Document Type
        </label>
        <input
          id="doctype-input"
          className="input"
          placeholder="e.g., Reports, PDFs"
          value={docType.join(", ")}
          onChange={(e) =>
            setDocType(
              e.currentTarget.value
                .split(",")
                .map((t) => t.trim())
                .filter(Boolean)
            )
          }
        />
      </motion.div>

      <motion.div variants={row}>
        <label className="text-sm font-medium" htmlFor="since-input">
          Since
        </label>
        <input
          id="since-input"
          type="date"
          className="input"
          value={since || ""}
          onChange={(e) => setSince(e.currentTarget.value || undefined)}
        />
      </motion.div>
    </motion.div>
  );
}
