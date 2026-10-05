"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, ApiError } from "@/lib/api";

import { PasteTextForm } from "./PasteTextForm";

export function LinkForm() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [showPaste, setShowPaste] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const job = await api.createRecipe({ url });
      router.push(`/jobs/${job.job_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={onSubmit} className="flex flex-col gap-3">
        <label htmlFor="link" className="sr-only">
          TikTok or Instagram Reel link
        </label>
        <input
          id="link"
          type="url"
          inputMode="url"
          className="input"
          placeholder="https://www.tiktok.com/@cook/video/…"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          aria-invalid={!!error}
          aria-describedby={error ? "link-error" : undefined}
          required
        />
        {error && (
          <p id="link-error" className="text-sm text-danger">
            {error}
          </p>
        )}
        <button type="submit" className="btn-primary" disabled={submitting || !url.trim()}>
          {submitting ? "Starting…" : "Make it a meal"}
        </button>
      </form>

      <div className="border-t border-border pt-5">
        {showPaste ? (
          <PasteTextForm autoFocus />
        ) : (
          <button
            type="button"
            className="text-sm font-semibold text-accent-ink underline-offset-4 hover:underline"
            onClick={() => setShowPaste(true)}
          >
            No link? Paste the recipe text instead
          </button>
        )}
      </div>
    </div>
  );
}
