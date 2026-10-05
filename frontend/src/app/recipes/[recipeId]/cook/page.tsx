import { redirect } from "next/navigation";

import { CookMode } from "@/components/cook/CookMode";

// Cook mode lives outside the (flow) group so it can use the full width:
// the current step on the left, the video on the right.
export default async function CookPage({ params, searchParams }: PageProps<"/recipes/[recipeId]/cook">) {
  const { recipeId } = await params;
  const { zip, owned, step } = await searchParams;
  if (typeof zip !== "string") redirect(`/recipes/${recipeId}/location`);
  const ownedIds = typeof owned === "string" && owned ? owned.split(",") : [];
  const initialStep = typeof step === "string" ? Number.parseInt(step, 10) || 1 : 1;

  return <CookMode recipeId={recipeId} zip={zip} owned={ownedIds} initialStep={initialStep} />;
}
