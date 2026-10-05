"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, ApiError } from "@/lib/api";

/** Fallback input: paste the caption or ingredient list when a link won't work. */
export function PasteTextForm({ autoFocus = false }: { autoFocus?: boolean }) {
  const router = useRouter();
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const job = await api.createRecipe({ text });
      router.push(`/jobs/${job.job_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-3">
      <label htmlFor="recipe-text" className="text-sm font-medium">
        Paste the caption, ingredient list, or recipe
      </label>
      <textarea
        id="recipe-text"
        className="input min-h-36 resize-y"
        placeholder={"1 lb chicken breast\n200g penne\n3 cloves garlic\n…"}
        value={text}
        onChange={(e) => setText(e.target.value)}
        autoFocus={autoFocus}
        required
      />
      {error && <p className="text-sm text-danger">{error}</p>}
      <button type="submit" className="btn-primary" disabled={submitting || !text.trim()}>
        {submitting ? "Starting…" : "Use this text"}
      </button>
    </form>
  );
}
