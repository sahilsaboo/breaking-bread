import { FlowSteps } from "@/components/FlowSteps";
import { JobProgress } from "@/components/JobProgress";

export default async function JobPage({ params }: PageProps<"/jobs/[jobId]">) {
  const { jobId } = await params;
  return (
    <>
      <FlowSteps current="Recipe" />
      <JobProgress jobId={jobId} />
    </>
  );
}
