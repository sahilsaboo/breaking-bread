"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api, ApiError, type MealPlan } from "@/lib/api";

import { Notice } from "../Notice";
import { CostSummary } from "./CostSummary";
import { GroceryList } from "./GroceryList";
import { MacrosPanel } from "./MacrosPanel";
import { StepList } from "./StepList";

export function Results({ recipeId, zip, owned }: { recipeId: string; zip: string; owned: string[] }) {
  const [plan, setPlan] = useState<MealPlan | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ownedKey = owned.join(",");

  useEffect(() => {
    api
      .planRecipe(recipeId, { zip_code: zip, owned_ingredient_ids: ownedKey ? ownedKey.split(",") : [] })
      .then(setPlan)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Something went wrong."));
  }, [recipeId, zip, ownedKey]);

  if (error) {
    return (
      <Notice tone="danger" title="We couldn't build your plan">
        {error}{" "}
        <Link href="/" className="font-medium underline">
          Start over
        </Link>
      </Notice>
    );
  }
  if (!plan) return <p className="text-muted">Building your grocery list…</p>;

  return (
    <div className="flex flex-col gap-10">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-balance">{plan.title}</h1>
        <p className="mt-2 text-sm text-muted">
          Prices near {plan.zip_code}
          {plan.source_url && (
            <>
              {" · "}
              <a href={plan.source_url} target="_blank" rel="noreferrer" className="underline underline-offset-4">
                Watch the original
              </a>
            </>
          )}
        </p>
      </header>

      <CostSummary plan={plan} />
      <GroceryList plan={plan} />
      <MacrosPanel plan={plan} />
      <StepList steps={plan.steps} />

      <div className="flex flex-wrap gap-3 border-t border-border pt-6">
        <Link href={`/recipes/${recipeId}/pantry?zip=${zip}`} className="btn-secondary">
          ← Change what I have
        </Link>
        <Link href="/" className="btn-secondary">
          Try another video
        </Link>
      </div>
    </div>
  );
}
