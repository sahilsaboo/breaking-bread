const STEPS = ["Link", "Recipe", "Location", "Pantry", "Your plan"] as const;

export type FlowStep = (typeof STEPS)[number];

/** Progress through the five screens of the flow. */
export function FlowSteps({ current }: { current: FlowStep }) {
  const currentIndex = STEPS.indexOf(current);
  return (
    <ol className="mb-8 flex items-center gap-1.5" aria-label="Progress">
      {STEPS.map((step, i) => (
        <li key={step} className="flex flex-1 flex-col gap-1.5">
          <span
            className={`h-1.5 rounded-full ${i <= currentIndex ? "bg-accent" : "bg-border"}`}
            aria-hidden
          />
          <span
            className={`text-xs ${i === currentIndex ? "font-semibold text-foreground" : "text-muted"}`}
            aria-current={i === currentIndex ? "step" : undefined}
          >
            {step}
          </span>
        </li>
      ))}
    </ol>
  );
}
