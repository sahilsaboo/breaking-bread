import type { ReactNode } from "react";

const TONES = {
  info: "bg-info-soft text-info",
  warn: "bg-warn-soft text-warn",
  danger: "bg-danger-soft text-danger",
  success: "bg-success-soft text-success",
} as const;

export function Notice({
  tone,
  title,
  children,
}: {
  tone: keyof typeof TONES;
  title?: string;
  children: ReactNode;
}) {
  return (
    <div className={`rounded-xl px-4 py-3 text-sm ${TONES[tone]}`} role={tone === "danger" ? "alert" : undefined}>
      {title && <p className="font-semibold">{title}</p>}
      <div className="text-foreground/90">{children}</div>
    </div>
  );
}
