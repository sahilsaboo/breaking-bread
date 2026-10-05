import { FlowSteps } from "@/components/FlowSteps";
import { LinkForm } from "@/components/LinkForm";

export default function Home() {
  return (
    <>
      <FlowSteps current="Link" />
      <h1 className="text-3xl font-bold tracking-tight text-balance">
        Saw a recipe you want to make?
      </h1>
      <p className="mt-3 mb-8 text-muted">
        Paste the TikTok or Reel. We&apos;ll turn it into a grocery list, tell you about what it
        costs, and walk you through cooking it step by step.
      </p>
      <LinkForm />
    </>
  );
}
