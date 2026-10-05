"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, ApiError, type Ingredient, type MealPlan, type Step } from "@/lib/api";
import { formatDuration } from "@/lib/format";
import { ingredientIllustration, stepIllustration, tintFor } from "@/lib/illustrations";
import type { IllustrationName } from "@/lib/illustrations.generated";

import { Illustration } from "../Illustration";
import { Notice } from "../Notice";
import { TermText } from "../results/TermText";
import { TimerControl } from "./TimerControl";
import { useStepTimers } from "./useStepTimers";
import { VideoPanel } from "./VideoPanel";

/** Ingredients whose name shows up in the step, e.g. "olive oil" in "Heat the olive oil". */
function ingredientsIn(step: Step, ingredients: Ingredient[]): Ingredient[] {
  const text = step.instruction.toLowerCase();
  return ingredients.filter((i) =>
    i.name
      .toLowerCase()
      .split(/\s+/)
      .some((word) => word.length >= 4 && text.includes(word)),
  );
}

export function CookMode({
  recipeId,
  zip,
  owned,
  initialStep,
}: {
  recipeId: string;
  zip: string;
  owned: string[];
  initialStep: number;
}) {
  const router = useRouter();
  const [plan, setPlan] = useState<MealPlan | null>(null);
  const [error, setError] = useState<string | null>(null);
  // 0-based; steps.length means "all done".
  const [index, setIndex] = useState(Math.max(0, initialStep - 1));
  const timers = useStepTimers();
  const ownedKey = owned.join(",");

  useEffect(() => {
    api
      .planRecipe(recipeId, { zip_code: zip, owned_ingredient_ids: ownedKey ? ownedKey.split(",") : [] })
      .then(setPlan)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Something went wrong."));
  }, [recipeId, zip, ownedKey]);

  const total = plan?.steps.length ?? 0;

  const goTo = useCallback(
    (next: number) => {
      if (!total) return;
      const clamped = Math.min(Math.max(next, 0), total);
      setIndex(clamped);
      // Keep the step in the URL so a refresh lands on the same step.
      const params = new URLSearchParams({ zip, step: String(clamped + 1) });
      if (ownedKey) params.set("owned", ownedKey);
      router.replace(`/recipes/${recipeId}/cook?${params}`, { scroll: false });
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    [total, zip, ownedKey, recipeId, router],
  );

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === "ArrowRight") goTo(index + 1);
      if (e.key === "ArrowLeft") goTo(index - 1);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [goTo, index]);

  const backToPlan = `/recipes/${recipeId}/results?${new URLSearchParams(
    ownedKey ? { zip, owned: ownedKey } : { zip },
  )}`;

  if (error) {
    return (
      <div className="mx-auto w-full max-w-xl px-4">
        <Notice tone="danger" title="We couldn't load the steps">
          {error}{" "}
          <Link href="/" className="font-medium underline">
            Start over
          </Link>
        </Notice>
      </div>
    );
  }
  if (!plan) return <p className="mx-auto max-w-xl px-4 text-muted">Getting your steps ready…</p>;

  const done = index >= total;
  const step = plan.steps[Math.min(index, total - 1)];
  const otherTimers = Object.entries(timers.timers).filter(
    ([order, t]) => Number(order) !== step.order && (t.endAt != null || t.remaining === 0),
  );

  return (
    <div className="mx-auto w-full max-w-6xl px-4 pb-32 lg:pb-12">
      {/* Top bar: back link, title, and one dot per step */}
      <div className="mb-5 flex flex-col gap-3">
        <div className="flex items-center justify-between gap-3">
          <Link href={backToPlan} className="text-sm font-semibold text-accent-ink hover:underline">
            ← Back to my plan
          </Link>
          <span className="truncate text-sm font-bold text-muted">{plan.title}</span>
        </div>
        <ol className="flex gap-1.5" aria-label="Steps">
          {plan.steps.map((s, i) => (
            <li key={s.order} className="flex-1">
              <button
                type="button"
                onClick={() => goTo(i)}
                aria-label={`Go to step ${s.order}`}
                aria-current={i === index ? "step" : undefined}
                className={`h-2.5 w-full rounded-full transition-colors ${
                  i === index ? "bg-sorbet" : i < index || done ? "bg-accent" : "bg-border hover:bg-accent-soft"
                }`}
              />
            </li>
          ))}
        </ol>
        {otherTimers.length > 0 && (
          <div className="flex flex-wrap gap-2" aria-label="Running timers">
            {otherTimers.map(([order, t]) => (
              <button
                key={order}
                type="button"
                onClick={() => goTo(Number(order) - 1)}
                className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-bold tabular-nums ${
                  t.remaining === 0 ? "animate-pulse bg-mint-soft text-success" : "bg-apricot-soft text-warn"
                }`}
              >
                <Illustration name="timer-clock" size={20} tint="bg-transparent" />
                Step {order}: {t.remaining === 0 ? "done!" : formatDuration(t.remaining)}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-start">
        {/* Video: pinned to the top on phones, on the right on wide screens. */}
        <aside className="sticky top-0 z-10 -mx-4 bg-background px-4 py-3 shadow-[0_8px_12px_-10px_rgb(35_48_66/0.25)] lg:top-6 lg:order-last lg:mx-0 lg:bg-transparent lg:p-0 lg:shadow-none">
          <VideoPanel
            sourceUrl={plan.source_url}
            start={done ? null : step.video_start_seconds}
            end={done ? null : step.video_end_seconds}
          />
        </aside>

        <section aria-live="polite">
          {done ? (
            <FinishedCard onRestart={() => goTo(0)} backToPlan={backToPlan} />
          ) : (
            <StepCard
              key={step.order}
              step={step}
              index={index}
              total={total}
              ingredients={ingredientsIn(step, plan.ingredients)}
              timer={step.timer_seconds != null ? timers.get(step.order, step.timer_seconds) : null}
              onStartTimer={() => timers.start(step.order, step.timer_seconds ?? 0)}
              onPauseTimer={() => timers.pause(step.order)}
              onResetTimer={() => timers.reset(step.order)}
            />
          )}

          {/* Back / Next: a fixed bar at thumb height on phones, under the card on desktop. */}
          {!done && (
            <nav className="fixed inset-x-0 bottom-0 z-20 flex gap-3 border-t border-border bg-card/95 px-4 py-3 backdrop-blur lg:static lg:mt-5 lg:border-0 lg:bg-transparent lg:p-0 lg:backdrop-blur-none">
              <button
                type="button"
                className="btn-secondary px-6 py-3"
                onClick={() => goTo(index - 1)}
                disabled={index === 0}
              >
                ← Back
              </button>
              <button type="button" className="btn-primary flex-1" onClick={() => goTo(index + 1)}>
                {index === total - 1 ? "I'm done!" : "Next step →"}
              </button>
            </nav>
          )}
        </section>
      </div>
    </div>
  );
}

function StepCard({
  step,
  index,
  total,
  ingredients,
  timer,
  onStartTimer,
  onPauseTimer,
  onResetTimer,
}: {
  step: Step;
  index: number;
  total: number;
  ingredients: Ingredient[];
  timer: ReturnType<ReturnType<typeof useStepTimers>["get"]> | null;
  onStartTimer: () => void;
  onPauseTimer: () => void;
  onResetTimer: () => void;
}) {
  return (
    <article className="card flex motion-safe:animate-step-in flex-col gap-5 p-6">
      <div className="flex items-center gap-4">
        <Illustration name={stepIllustration(step.instruction)} size={72} tint={tintFor(index)} />
        <span className="rounded-full bg-sorbet-soft px-3 py-1 text-sm font-bold text-sorbet-ink">
          Step {step.order} of {total}
        </span>
      </div>

      <p className="text-2xl leading-snug font-semibold text-balance">
        <TermText text={step.instruction} terms={step.terms ?? []} />
      </p>

      {ingredients.length > 0 && (
        <ul className="flex flex-wrap gap-2" aria-label="Ingredients in this step">
          {ingredients.map((ing, i) => (
            <li
              key={ing.id}
              className="flex items-center gap-1.5 rounded-full border border-border bg-card py-1 pr-3 pl-1 text-sm font-semibold capitalize"
            >
              <Illustration name={ingredientIllustration(ing.name)} size={28} tint={tintFor(i + 1)} className="rounded-full" />
              {ing.name}
            </li>
          ))}
        </ul>
      )}

      {timer && <TimerControl timer={timer} onStart={onStartTimer} onPause={onPauseTimer} onReset={onResetTimer} />}

      {step.doneness_cue && (
        <Callout picture="magnifying-glass-tilted-left" label="It's ready when" className="bg-mint-soft">
          {step.doneness_cue}
        </Callout>
      )}
      {step.safety_note && (
        <Callout picture="thermometer" label="Stay safe" className="bg-sorbet-soft">
          {step.safety_note}
        </Callout>
      )}
      {step.equipment_swap && (
        <Callout picture="spoon" label="Don't have it?" className="bg-sky-soft">
          {step.equipment_swap}
        </Callout>
      )}
    </article>
  );
}

function Callout({
  picture,
  label,
  className,
  children,
}: {
  picture: IllustrationName;
  label: string;
  className: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`flex items-start gap-3 rounded-2xl p-3 ${className}`}>
      <Illustration name={picture} size={40} tint="bg-card" />
      <p className="pt-1.5">
        <span className="font-bold">{label}: </span>
        {children}
      </p>
    </div>
  );
}

function FinishedCard({ onRestart, backToPlan }: { onRestart: () => void; backToPlan: string }) {
  return (
    <article className="card flex motion-safe:animate-step-in flex-col items-center gap-4 p-8 text-center">
      <Illustration name="party-popper" size={96} tint="bg-apricot-soft" />
      <h1 className="text-3xl font-extrabold tracking-tight">You cooked it!</h1>
      <p className="text-muted">Enjoy your meal. Put leftovers in the fridge within 2 hours.</p>
      <div className="flex flex-wrap justify-center gap-3">
        <button type="button" className="btn-secondary" onClick={onRestart}>
          See the steps again
        </button>
        <Link href={backToPlan} className="btn-secondary">
          Back to my plan
        </Link>
        <Link href="/" className="btn-secondary">
          Try another video
        </Link>
      </div>
    </article>
  );
}
