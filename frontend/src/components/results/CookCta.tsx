import Link from "next/link";

import type { Step } from "@/lib/api";
import { stepIllustration } from "@/lib/illustrations";

import { MonoIllustration } from "../Illustration";

/** Invites the user into cook mode, with a peek at what the steps involve. */
export function CookCta({ steps, href }: { steps: Step[]; href: string }) {
  const timedMinutes = Math.round(steps.reduce((sum, s) => sum + (s.timer_seconds ?? 0), 0) / 60);

  return (
    <section aria-labelledby="cook-heading" className="card flex flex-col gap-4 bg-gradient-to-br from-sky-soft to-sorbet-soft">
      <div>
        <h2 id="cook-heading" className="text-xl font-extrabold tracking-tight">
          Ready to cook?
        </h2>
        <p className="mt-1 text-sm text-muted">
          {steps.length} short steps, one at a time, with the video playing alongside
          {timedMinutes > 0 && ` and built-in timers (about ${timedMinutes} min of cooking)`}.
        </p>
      </div>
      <ol className="flex flex-wrap gap-2.5 pt-1" aria-hidden>
        {steps.map((s, i) => (
          <li key={s.order} className="relative">
            <MonoIllustration name={stepIllustration(s.instruction)} size={52} className="border-2 border-accent-soft" />
            <span className={`absolute -top-1 -right-1 grid size-5 place-items-center rounded-full bg-accent text-[0.65rem] font-bold text-accent-fg`}>
              {s.order}
            </span>
          </li>
        ))}
      </ol>
      <Link href={href} className="btn-primary">
        Start cooking →
      </Link>
    </section>
  );
}
