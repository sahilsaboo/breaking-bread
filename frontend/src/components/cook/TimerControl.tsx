import { formatDuration } from "@/lib/format";

import { Illustration } from "../Illustration";
import type { StepTimer } from "./useStepTimers";

/** The big timer built into a step card. */
export function TimerControl({
  timer,
  onStart,
  onPause,
  onReset,
}: {
  timer: StepTimer;
  onStart: () => void;
  onPause: () => void;
  onReset: () => void;
}) {
  const running = timer.endAt != null;
  const finished = timer.remaining === 0;
  const untouched = timer.remaining === timer.duration && !running;
  const progress = 1 - timer.remaining / timer.duration;

  return (
    <div
      className={`relative flex items-center gap-4 overflow-hidden rounded-3xl p-4 ${
        finished ? "bg-mint-soft" : "bg-apricot-soft"
      }`}
    >
      {/* Fills left to right as time passes. */}
      <span
        className="absolute inset-y-0 left-0 bg-apricot/40 transition-[width] duration-300"
        style={{ width: `${finished ? 0 : progress * 100}%` }}
        aria-hidden
      />
      <Illustration name={finished ? "check-mark-button" : "timer-clock"} size={52} tint="bg-card" className="relative" />
      <div className="relative flex flex-col">
        <span className="text-xs font-bold tracking-wide text-muted uppercase">Timer</span>
        <span className="font-mono text-3xl font-bold tabular-nums" aria-live="polite">
          {finished ? "Time's up!" : formatDuration(timer.remaining)}
        </span>
      </div>
      <div className="relative ml-auto flex gap-2">
        {!finished && (
          <button
            type="button"
            className="btn-primary w-auto px-5 py-2 text-sm"
            onClick={running ? onPause : onStart}
          >
            {running ? "Pause" : untouched ? "Start" : "Resume"}
          </button>
        )}
        {!untouched && (
          <button type="button" className="btn-secondary py-2 text-sm" onClick={onReset}>
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
