"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type StepTimer = {
  duration: number;
  remaining: number;
  /** When it will hit zero (ms since epoch) while running; null when paused or stopped. */
  endAt: number | null;
};

type Timers = Record<number, StepTimer>;

function chime() {
  try {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1);
    osc.connect(gain).connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 1);
  } catch {
    // Audio is a nice-to-have; the on-screen message still shows.
  }
  navigator.vibrate?.([200, 100, 200]);
}

/**
 * Timers for every step, keyed by step number. They live above the step view
 * so a 10-minute pasta timer keeps running while you move on to the next step.
 */
export function useStepTimers() {
  const [timers, setTimers] = useState<Timers>({});
  // The ticking interval and the buttons both write through `update`, which
  // keeps this ref current, so a tick can never undo a pause or reset.
  const latest = useRef<Timers>({});

  const update = useCallback((fn: (prev: Timers) => Timers) => {
    latest.current = fn(latest.current);
    setTimers(latest.current);
  }, []);

  const anyRunning = Object.values(timers).some((t) => t.endAt != null);

  useEffect(() => {
    if (!anyRunning) return;
    const id = setInterval(() => {
      const now = Date.now();
      let finished = false;
      update((prev) => {
        const next = { ...prev };
        for (const [step, t] of Object.entries(prev)) {
          if (t.endAt == null) continue;
          const remaining = Math.max(0, Math.ceil((t.endAt - now) / 1000));
          if (remaining === 0) finished = true;
          next[Number(step)] = { ...t, remaining, endAt: remaining === 0 ? null : t.endAt };
        }
        return next;
      });
      if (finished) chime();
    }, 250);
    return () => clearInterval(id);
  }, [anyRunning, update]);

  const get = useCallback(
    (step: number, duration: number): StepTimer =>
      timers[step] ?? { duration, remaining: duration, endAt: null },
    [timers],
  );

  const start = useCallback(
    (step: number, duration: number) =>
      update((prev) => {
        const t = prev[step];
        const remaining = !t || t.remaining === 0 ? duration : t.remaining;
        return { ...prev, [step]: { duration, remaining, endAt: Date.now() + remaining * 1000 } };
      }),
    [update],
  );

  const pause = useCallback(
    (step: number) =>
      update((prev) => (prev[step] ? { ...prev, [step]: { ...prev[step], endAt: null } } : prev)),
    [update],
  );

  const reset = useCallback(
    (step: number) =>
      update((prev) => {
        const next = { ...prev };
        delete next[step];
        return next;
      }),
    [update],
  );

  return { timers, get, start, pause, reset };
}
