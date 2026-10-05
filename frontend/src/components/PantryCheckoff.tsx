"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, ApiError, type Recipe } from "@/lib/api";
import { amountLabel, SOURCE_LABELS } from "@/lib/format";

import { Notice } from "./Notice";

/** Below this, ask the user to double-check the ingredient. */
const LOW_CONFIDENCE = 0.7;

export function PantryCheckoff({ recipeId, zip }: { recipeId: string; zip: string }) {
  const router = useRouter();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [owned, setOwned] = useState<Set<string>>(new Set());

  useEffect(() => {
    api
      .getRecipe(recipeId)
      .then(setRecipe)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Something went wrong."));
  }, [recipeId]);

  function toggle(id: string) {
    setOwned((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function onContinue() {
    const params = new URLSearchParams({ zip });
    if (owned.size) params.set("owned", [...owned].join(","));
    router.push(`/recipes/${recipeId}/results?${params}`);
  }

  if (error) {
    return (
      <Notice tone="danger" title="We lost this recipe">
        {error}{" "}
        <Link href="/" className="font-medium underline">
          Start over
        </Link>
      </Notice>
    );
  }
  if (!recipe) return <p className="text-muted">Loading ingredients…</p>;

  const needsCheck = recipe.ingredients.some((i) => i.confidence < LOW_CONFIDENCE);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-sm font-medium text-accent">{recipe.title}</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">What do you already have?</h1>
        <p className="mt-2 text-muted">
          Tap everything that&apos;s already in your kitchen. We&apos;ll leave it off your grocery list.
        </p>
      </div>

      {needsCheck && (
        <Notice tone="warn" title="Double-check the flagged items">
          Some ingredients weren&apos;t said clearly in the video. Compare them with the video before you
          shop.
        </Notice>
      )}

      <ul className="card flex flex-col divide-y divide-border p-0">
        {recipe.ingredients.map((i) => {
          const checked = owned.has(i.id);
          return (
            <li key={i.id}>
              <label className="flex cursor-pointer items-start gap-3 px-5 py-4 hover:bg-accent-soft/50">
                <input
                  type="checkbox"
                  className="mt-1 size-5 shrink-0 accent-accent"
                  checked={checked}
                  onChange={() => toggle(i.id)}
                />
                <span className="flex flex-1 flex-col gap-0.5">
                  <span className={`font-medium capitalize ${checked ? "text-muted line-through" : ""}`}>
                    {i.name}
                  </span>
                  <span className="text-sm text-muted">
                    {amountLabel(i)}
                    {i.estimated && " (estimated)"} · {SOURCE_LABELS[i.source]}
                  </span>
                </span>
                {i.confidence < LOW_CONFIDENCE && (
                  <span className="shrink-0 rounded-full bg-warn-soft px-2 py-0.5 text-xs font-medium text-warn">
                    Double-check
                  </span>
                )}
              </label>
            </li>
          );
        })}
      </ul>

      <button type="button" className="btn-primary" onClick={onContinue}>
        Build my grocery list
        {owned.size > 0 && <span className="font-normal opacity-80">({owned.size} owned)</span>}
      </button>
    </div>
  );
}
