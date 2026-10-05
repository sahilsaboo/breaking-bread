"use client";

import { useEffect, useRef, useState } from "react";

import { formatDuration } from "@/lib/format";

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

/** Tappable countdown for a timed step. */
export function StepTimer({ seconds }: { seconds: number }) {
  const [remaining, setRemaining] = useState(seconds);
  const [running, setRunning] = useState(false);
  const endAt = useRef(0);

  useEffect(() => {
    if (!running) return;
    endAt.current = Date.now() + remaining * 1000;
    const id = setInterval(() => {
      const left = Math.max(0, Math.ceil((endAt.current - Date.now()) / 1000));
      setRemaining(left);
      if (left === 0) {
        clearInterval(id);
        setRunning(false);
        chime();
      }
    }, 250);
    return () => clearInterval(id);
    // Only restart the interval when starting or pausing, not on every tick.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [running]);

  const finished = remaining === 0;

  return (
    <div
      className={`flex items-center gap-3 rounded-xl px-3 py-2 ${finished ? "bg-success-soft" : "bg-accent-soft"}`}
    >
      <span className="font-mono text-lg font-semibold tabular-nums" aria-live="polite">
        {finished ? "Time's up!" : formatDuration(remaining)}
      </span>
      <div className="ml-auto flex gap-2">
        {!finished && (
          <button type="button" className="btn-secondary py-1 text-sm" onClick={() => setRunning((r) => !r)}>
            {running ? "Pause" : remaining === seconds ? "Start timer" : "Resume"}
          </button>
        )}
        {(remaining !== seconds || finished) && (
          <button
            type="button"
            className="btn-secondary py-1 text-sm"
            onClick={() => {
              setRunning(false);
              setRemaining(seconds);
            }}
          >
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
