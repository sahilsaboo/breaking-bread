import type { MealPlan } from "@/lib/api";

export function MacrosPanel({ plan }: { plan: MealPlan }) {
  const m = plan.macros_per_serving;
  const tiles = [
    { label: "Calories", value: Math.round(m.calories), unit: "", tint: "bg-apricot-soft" },
    { label: "Protein", value: Math.round(m.protein_g), unit: "g", tint: "bg-sorbet-soft" },
    { label: "Carbs", value: Math.round(m.carbs_g), unit: "g", tint: "bg-sky-soft" },
    { label: "Fat", value: Math.round(m.fat_g), unit: "g", tint: "bg-mint-soft" },
  ];

  return (
    <section aria-labelledby="macros-heading" className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <h2 id="macros-heading" className="text-xl font-extrabold tracking-tight">
          Per serving
        </h2>
        {m.approximate && <span className="text-xs text-muted">Approximate</span>}
      </div>
      <dl className="grid grid-cols-4 gap-2">
        {tiles.map((t) => (
          <div key={t.label} className={`flex flex-col items-center gap-0.5 rounded-2xl px-2 py-3 ${t.tint}`}>
            <dt className="text-xs text-muted">{t.label}</dt>
            <dd className="text-lg font-bold tabular-nums">
              {m.approximate && "~"}
              {t.value}
              <span className="text-sm font-medium">{t.unit}</span>
            </dd>
          </div>
        ))}
      </dl>
      <p className="text-xs text-muted">
        {plan.servings.estimated
          ? `The video didn't say how many people it serves, so we assumed ${plan.servings.value}.`
          : `Makes ${plan.servings.value} servings.`}
      </p>
    </section>
  );
}
