import type { Ingredient, Stage } from "./api";

/** Costs are always estimates, so money always carries a "~". */
export function approxMoney(amount: number): string {
  return `~$${amount.toFixed(2)}`;
}

export function amountLabel(i: Ingredient): string {
  if (i.quantity == null) return i.unit ?? "";
  const qty = Number.isInteger(i.quantity) ? String(i.quantity) : fraction(i.quantity);
  return [qty, i.unit].filter(Boolean).join(" ");
}

function fraction(n: number): string {
  const whole = Math.floor(n);
  const rest = n - whole;
  const known: [number, string][] = [
    [0.25, "¼"],
    [0.33, "⅓"],
    [0.5, "½"],
    [0.67, "⅔"],
    [0.75, "¾"],
  ];
  const match = known.find(([v]) => Math.abs(v - rest) < 0.02);
  if (!match) return String(Math.round(n * 100) / 100);
  return whole ? `${whole}${match[1]}` : match[1];
}

export const SOURCE_LABELS: Record<Ingredient["source"], string> = {
  caption: "from the caption",
  transcript: "heard in the video",
  frames: "seen on screen",
  pasted: "from your text",
  inferred: "our best guess",
};

export const STAGE_LABELS: Record<Stage, string> = {
  metadata: "Reading the caption",
  audio: "Listening to the video",
  frames: "Reading text on screen",
  merge: "Putting the recipe together",
};

export function formatDuration(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}
