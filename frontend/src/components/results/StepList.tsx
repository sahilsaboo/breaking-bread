import type { Step } from "@/lib/api";

import { StepTimer } from "./StepTimer";
import { TermText } from "./TermText";

export function StepList({ steps }: { steps: Step[] }) {
  return (
    <section aria-labelledby="steps-heading" className="flex flex-col gap-4">
      <div>
        <h2 id="steps-heading" className="text-xl font-bold tracking-tight">
          Let&apos;s cook
        </h2>
        <p className="mt-1 text-sm text-muted">One thing at a time. Tap underlined words to see what they mean.</p>
      </div>
      <ol className="flex flex-col gap-3">
        {steps.map((step) => (
          <li key={step.order} className="card flex gap-4">
            <span className="grid size-8 shrink-0 place-items-center rounded-full bg-accent text-sm font-bold text-accent-fg">
              {step.order}
            </span>
            <div className="flex flex-1 flex-col gap-3">
              <p className="leading-relaxed">
                <TermText text={step.instruction} terms={step.terms ?? []} />
              </p>
              {step.timer_seconds != null && <StepTimer seconds={step.timer_seconds} />}
              {step.doneness_cue && (
                <Callout icon="👀" label="It's ready when" className="bg-success-soft">
                  {step.doneness_cue}
                </Callout>
              )}
              {step.safety_note && (
                <Callout icon="⚠️" label="Stay safe" className="bg-danger-soft">
                  {step.safety_note}
                </Callout>
              )}
              {step.equipment_swap && (
                <Callout icon="🔁" label="Don't have it?" className="bg-info-soft">
                  {step.equipment_swap}
                </Callout>
              )}
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

function Callout({
  icon,
  label,
  className,
  children,
}: {
  icon: string;
  label: string;
  className: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`flex gap-2 rounded-xl px-3 py-2 text-sm ${className}`}>
      <span aria-hidden>{icon}</span>
      <p>
        <span className="font-semibold">{label}: </span>
        {children}
      </p>
    </div>
  );
}
