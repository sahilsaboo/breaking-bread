import type { IllustrationName } from "./illustrations.generated";

// Picks a picture for an ingredient or step by keyword. First match wins, so
// specific words ("bell pepper", "olive oil") come before general ones.
type Rule = [RegExp, IllustrationName];

const INGREDIENT_RULES: Rule[] = [
  [/chicken|turkey|poultry/, "poultry-leg"],
  [/bacon|pancetta/, "bacon"],
  [/beef|steak|pork|lamb|sausage|meat/, "cut-of-meat"],
  [/shrimp|prawn/, "shrimp"],
  [/fish|salmon|tuna|cod|tilapia/, "fish"],
  [/\begg/, "egg"],
  [/pasta|penne|spaghetti|noodle|macaroni|linguine|fettuccine|rigatoni|orzo/, "spaghetti"],
  [/rice/, "cooked-rice"],
  [/bread|tortilla|bun|baguette|pita/, "bread"],
  [/garlic/, "garlic"],
  [/onion|shallot|scallion|leek/, "onion"],
  [/basil|cilantro|parsley|thyme|rosemary|oregano|dill|mint|herb/, "herb"],
  [/spinach|lettuce|kale|cabbage|arugula|greens/, "leafy-green"],
  [/tomato/, "tomato"],
  [/carrot/, "carrot"],
  [/potato/, "potato"],
  [/mushroom/, "mushroom"],
  [/broccoli/, "broccoli"],
  [/bell pepper/, "bell-pepper"],
  [/chil[ei]|jalape|pepper flake|sriracha|hot sauce/, "hot-pepper"],
  [/salt|pepper|spice|paprika|cumin|seasoning/, "salt"],
  [/lemon|lime/, "lemon"],
  [/avocado/, "avocado"],
  [/corn/, "ear-of-corn"],
  [/cucumber/, "cucumber"],
  [/butter/, "butter"],
  [/cheese|parmesan|mozzarella|cheddar|feta|ricotta/, "cheese-wedge"],
  [/cream|milk|yogurt/, "glass-of-milk"],
  [/oil/, "olive"],
  [/honey|sugar|syrup/, "honey-pot"],
  [/water|broth|stock/, "droplet"],
  [/bean|chickpea|lentil|canned/, "canned-food"],
];

// Cooking methods come before prep words, so "add the minced garlic to the
// skillet" shows a pan, not a knife.
const STEP_RULES: Rule[] = [
  [/drain|pasta water/, "droplet"],
  [/\b(boil|boiling|pot)\b/, "pot-of-food"],
  [/skillet|pan\b|sear|fry|saut|melt|simmer|wilt/, "shallow-pan-of-food"],
  [/oven|bake|roast|broil/, "fire"],
  [/\b(cut|chop|dice|slice|mince)/, "kitchen-knife"],
  [/\b(mix|stir|whisk|bowl|toss)/, "bowl-with-spoon"],
  [/\b(serve|plate|enjoy)/, "fork-and-knife-with-plate"],
];

function match(text: string, rules: Rule[], fallback: IllustrationName): IllustrationName {
  const lower = text.toLowerCase();
  return rules.find(([pattern]) => pattern.test(lower))?.[1] ?? fallback;
}

export const ingredientIllustration = (name: string) => match(name, INGREDIENT_RULES, "bowl-with-spoon");
export const stepIllustration = (instruction: string) => match(instruction, STEP_RULES, "cooking");

/** Pastel backgrounds that rotate so a list of pictures doesn't look flat. */
export const TINTS = ["bg-sky-soft", "bg-sorbet-soft", "bg-apricot-soft", "bg-mint-soft"] as const;
export const tintFor = (index: number) => TINTS[index % TINTS.length];
