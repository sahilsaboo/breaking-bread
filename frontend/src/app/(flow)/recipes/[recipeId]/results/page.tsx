import { redirect } from "next/navigation";

import { FlowSteps } from "@/components/FlowSteps";
import { Results } from "@/components/results/Results";

export default async function ResultsPage({
  params,
  searchParams,
}: PageProps<"/recipes/[recipeId]/results">) {
  const { recipeId } = await params;
  const { zip, owned } = await searchParams;
  if (typeof zip !== "string") redirect(`/recipes/${recipeId}/location`);
  const ownedIds = typeof owned === "string" && owned ? owned.split(",") : [];

  return (
    <>
      <FlowSteps current="Your plan" />
      <Results recipeId={recipeId} zip={zip} owned={ownedIds} />
    </>
  );
}
