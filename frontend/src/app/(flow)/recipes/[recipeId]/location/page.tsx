import { FlowSteps } from "@/components/FlowSteps";
import { LocationForm } from "@/components/LocationForm";

export default async function LocationPage({ params }: PageProps<"/recipes/[recipeId]/location">) {
  const { recipeId } = await params;
  return (
    <>
      <FlowSteps current="Location" />
      <h1 className="text-2xl font-bold tracking-tight">Where do you shop?</h1>
      <p className="mt-2 mb-6 text-muted">Prices change from place to place.</p>
      <LocationForm recipeId={recipeId} />
    </>
  );
}
