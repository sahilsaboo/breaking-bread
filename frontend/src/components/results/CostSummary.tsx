import type { MealPlan } from "@/lib/api";
import { approxMoney } from "@/lib/format";

import { MonoIllustration } from "../Illustration";

export function CostSummary({ plan }: { plan: MealPlan }) {
  const allEstimates = plan.grocery_list.every((g) => g.product.price_type === "estimate");
  return (
    <section aria-label="Cost" className="flex flex-col gap-2">
      <div className="grid grid-cols-2 gap-3">
        <div className="card flex flex-col gap-1 border-accent bg-accent text-accent-fg">
          <MonoIllustration name="shopping-cart" size={44} className="mb-1" />
          <span className="text-sm font-bold text-accent-fg/85">Trip cost</span>
          <span className="text-3xl font-bold tracking-tight">{approxMoney(plan.costs.trip_total)}</span>
          <span className="text-xs text-accent-fg/85">What you&apos;ll spend at the store</span>
        </div>
        <div className="card flex flex-col gap-1 border-accent bg-accent text-accent-fg">
          <MonoIllustration name="fork-and-knife-with-plate" size={44} className="mb-1" />
          <span className="text-sm font-bold text-accent-fg/85">Per meal</span>
          <span className="text-3xl font-bold tracking-tight">{approxMoney(plan.costs.per_meal)}</span>
          <span className="text-xs text-accent-fg/85">
            What one serving really costs, counting what you have
          </span>
        </div>
      </div>
      <p className="text-xs text-muted">
        {allEstimates
          ? "These are estimated prices. Real prices vary by store."
          : "Prices are approximate and can change at the store."}
      </p>
    </section>
  );
}
