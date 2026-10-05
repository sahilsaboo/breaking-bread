"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, ApiError, type Job } from "@/lib/api";
import { STAGE_LABELS } from "@/lib/format";
import type { IllustrationName } from "@/lib/illustrations.generated";

import { Illustration } from "./Illustration";

import { Notice } from "./Notice";
import { PasteTextForm } from "./PasteTextForm";

const POLL_MS = 1500;

const STAGE_PICTURES: Record<Job["stages"][number], IllustrationName> = {
  metadata: "magnifying-glass-tilted-left",
  audio: "clapper-board",
  frames: "sparkles",
  merge: "cooking",
};

export function JobProgress({ jobId }: { jobId: string }) {
  const router = useRouter();
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    async function poll() {
      try {
        const next = await api.getJob(jobId);
        if (cancelled) return;
        setJob(next);
        if (next.status === "done" && next.recipe_id) {
          router.replace(`/recipes/${next.recipe_id}/location`);
        } else if (next.status === "running") {
          timer = setTimeout(poll, POLL_MS);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Something went wrong.");
      }
    }

    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [jobId, router]);

  const failed = job?.status === "failed" || error;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">
          {failed ? "We couldn't read that video" : "Finding the recipe…"}
        </h1>
        {!failed && (
          <p className="mt-2 text-muted">This can take up to a minute or two. Hang tight.</p>
        )}
      </div>

      {job && (
        <ol className="card flex flex-col gap-3" aria-live="polite">
          {job.stages.map((stage) => {
            const done = job.completed_stages.includes(stage);
            const active = job.stage === stage;
            const stageFailed = active && job.status === "failed";
            return (
              <li key={stage} className="flex items-center gap-3">
                <Illustration
                  name={STAGE_PICTURES[stage]}
                  size={40}
                  tint={done ? "bg-mint-soft" : active ? "bg-sky-soft" : "bg-background"}
                  className={done || active ? "" : "opacity-50 grayscale"}
                />
                <span className={`flex-1 ${done || active ? "font-semibold text-foreground" : "text-muted"}`}>
                  {STAGE_LABELS[stage]}
                </span>
                <StageIcon state={stageFailed ? "failed" : done ? "done" : active ? "active" : "pending"} />
              </li>
            );
          })}
        </ol>
      )}

      {failed && (
        <>
          <Notice tone="danger" title="That didn't work">
            {job?.error ?? error}
          </Notice>
          <div className="card">
            <PasteTextForm />
          </div>
        </>
      )}
    </div>
  );
}

function StageIcon({ state }: { state: "done" | "active" | "pending" | "failed" }) {
  if (state === "done") {
    return (
      <span className="grid size-6 place-items-center rounded-full bg-success text-xs text-white" aria-label="Done">
        ✓
      </span>
    );
  }
  if (state === "failed") {
    return (
      <span className="grid size-6 place-items-center rounded-full bg-danger text-xs text-white" aria-label="Failed">
        ✕
      </span>
    );
  }
  if (state === "active") {
    return (
      <span
        className="size-6 animate-spin rounded-full border-2 border-accent border-t-transparent"
        aria-label="In progress"
      />
    );
  }
  return <span className="size-6 rounded-full border-2 border-border" aria-label="Not started" />;
}
