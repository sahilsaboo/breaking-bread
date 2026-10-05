import { redirect } from "next/navigation";

import { FlowSteps } from "@/components/FlowSteps";
import { PantryCheckoff } from "@/components/PantryCheckoff";

export default async function PantryPage({
  params,
  searchParams,
}: PageProps<"/recipes/[recipeId]/pantry">) {
  const { recipeId } = await params;
  const { zip } = await searchParams;
  if (typeof zip !== "string") redirect(`/recipes/${recipeId}/location`);

  return (
    <>
      <FlowSteps current="Pantry" />
      <PantryCheckoff recipeId={recipeId} zip={zip} />
    </>
  );
}
