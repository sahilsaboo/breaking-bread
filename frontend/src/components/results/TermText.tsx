"use client";

import { useState } from "react";

import type { Step } from "@/lib/api";

type Term = NonNullable<Step["terms"]>[number];

function escapeRegExp(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Renders an instruction with each cooking term tappable to show its definition. */
export function TermText({ text, terms }: { text: string; terms: Term[] }) {
  if (terms.length === 0) return <>{text}</>;

  const byLower = new Map(terms.map((t) => [t.term.toLowerCase(), t]));
  const pattern = new RegExp(`(${terms.map((t) => escapeRegExp(t.term)).join("|")})`, "gi");

  return (
    <>
      {text.split(pattern).map((part, i) => {
        const term = byLower.get(part.toLowerCase());
        return term ? <TermButton key={i} label={part} definition={term.definition} /> : part;
      })}
    </>
  );
}

/** "Cooked through." -> "cooked through", so it reads naturally in parentheses. */
function asAside(definition: string) {
  const trimmed = definition.trim().replace(/\.$/, "");
  return trimmed.charAt(0).toLowerCase() + trimmed.slice(1);
}

function TermButton({ label, definition }: { label: string; definition: string }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        type="button"
        className="font-semibold text-accent-ink underline decoration-sorbet decoration-dotted decoration-2 underline-offset-4"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        title={definition}
      >
        {label}
      </button>
      {open && <span className="text-muted"> ({asAside(definition)})</span>}
    </>
  );
}
