import { FlowSteps } from "@/components/FlowSteps";
import { Illustration } from "@/components/Illustration";
import { LinkForm } from "@/components/LinkForm";
import type { IllustrationName } from "@/lib/illustrations.generated";

const HOW_IT_WORKS: { picture: IllustrationName; label: string; tint: string; tilt: string }[] = [
  { picture: "clapper-board", label: "Paste a video", tint: "bg-sky-soft", tilt: "-rotate-3" },
  { picture: "shopping-cart", label: "Get a grocery list", tint: "bg-sorbet-soft", tilt: "rotate-2" },
  { picture: "money-bag", label: "See what it costs", tint: "bg-apricot-soft", tilt: "-rotate-2" },
  { picture: "cooking", label: "Cook step by step", tint: "bg-mint-soft", tilt: "rotate-3" },
];

export default function Home() {
  return (
    <>
      <FlowSteps current="Link" />
      <h1 className="text-4xl font-extrabold tracking-tight text-balance">
        Saw a recipe you want to make?
      </h1>
      <p className="mt-3 text-muted">
        Paste the TikTok or Reel. We&apos;ll turn it into a grocery list, tell you about what it
        costs, and walk you through cooking it step by step.
      </p>
      <ul className="my-8 grid grid-cols-4 gap-2" aria-label="How it works">
        {HOW_IT_WORKS.map((s) => (
          <li key={s.label} className="flex flex-col items-center gap-2 text-center">
            <Illustration name={s.picture} size={64} tint={s.tint} className={`${s.tilt} shadow-sm`} />
            <span className="text-xs font-bold text-muted">{s.label}</span>
          </li>
        ))}
      </ul>
      <LinkForm />
    </>
  );
}
