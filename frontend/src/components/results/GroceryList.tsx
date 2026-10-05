import type { MealPlan } from "@/lib/api";
import { approxMoney } from "@/lib/format";

export function GroceryList({ plan }: { plan: MealPlan }) {
  const owned = plan.ingredients.filter((i) => i.owned);
  return (
    <section aria-labelledby="grocery-heading" className="flex flex-col gap-3">
      <h2 id="grocery-heading" className="text-xl font-bold tracking-tight">
        Grocery list
      </h2>

      {plan.grocery_list.length === 0 ? (
        <p className="card text-muted">You already have everything. Nice!</p>
      ) : (
        <ul className="card flex flex-col divide-y divide-border p-0">
          {plan.grocery_list.map((item) => (
            <li key={item.ingredient_id} className="flex items-start gap-3 px-5 py-3">
              <div className="flex flex-1 flex-col">
                <span className="font-medium">
                  {item.packages > 1 && `${item.packages} × `}
                  {item.product.product_name}
                </span>
                <span className="text-sm text-muted">
                  for {item.name} · {item.product.store_name}
                </span>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1">
                <span className="font-semibold tabular-nums">{approxMoney(item.line_total)}</span>
                <PriceTag type={item.product.price_type} />
              </div>
            </li>
          ))}
        </ul>
      )}

      {owned.length > 0 && (
        <p className="text-sm text-muted">
          Already have: {owned.map((i) => i.name).join(", ")}
        </p>
      )}
    </section>
  );
}

function PriceTag({ type }: { type: "store price" | "estimate" }) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
        type === "store price" ? "bg-success-soft text-success" : "bg-warn-soft text-warn"
      }`}
    >
      {type}
    </span>
  );
}
