# Breaking Bread: Product Brief

AI Builder Space Proseminar
Sarah Fattah, Sahil Saboo, Brendan Schemer | September 30, 2026

Breaking Bread is an AI-powered cooking companion, delivered as a web and mobile app, that helps college students new to apartment life turn a TikTok or reel they saw into a meal they can shop for, afford, and cook. It brings grocery lists, cost estimates, nutrition information, and beginner-friendly guidance into one simple experience.

## The Idea & The User

Breaking Bread is an AI-powered cooking companion for college students early in their off-campus apartment life, who are often inexperienced in the kitchen. From personal experience and conversations with peers, the team has seen that these students overcomplicate cooking in their heads. The result is either overspending on groceries or giving up and ordering in. Breaking Bread simplifies the whole process in one place: recommending recipes based on goals, likes, and dislikes; building a grocery list and tracking costs; and guiding the user through cooking step by step. Users can start from built-in recipes, a TikTok or reel they saw, or simply by sharing what they already have in their fridge and pantry. This is a better version of something that exists: similar tools are on the market, but the team has not seen one that integrates shopping, budgeting, and simplified cooking into a single experience.

## Does this exist already?

Several apps already cover parts of this. Saffie, ChefTime, and Savora import recipes from TikTok and Instagram and turn them into meal plans and grocery lists, with Saffie sending lists directly to Instacart. MyMealStream and Mealift focus on macros, while CostBite and Budget Bites focus on cost per meal and weekly spend. Established tools such as Samsung Food, Paprika, AnyList, and Plan to Eat are more mature but weaker on social import and cost tracking. Each does a piece well, but none has combined real budgeting, nutrition information, and beginner-friendly cooking guidance into one platform built for inexperienced cooks. That gap is Breaking Bread's differentiator. The team is also building it on purpose, to learn how to build a product with real-world integrations and applications.

## Scope for this sprint

For the three-week sprint, the team will build one end-to-end flow: a user pastes a TikTok or reel link, and Breaking Bread turns it into a meal they can shop for and cook.

### Must-haves
- Start from a pasted TikTok or reel link
- Identify the ingredients and generate a grocery list
- Estimated cost of the meal
- Per-meal macronutrients
- Step-by-step, beginner-friendly cooking guidance
- Delivered as a web app

### Stretch goal
- Show nearby stores where the user can buy the ingredients

### Out of scope
- Built-in recipe library
- Fridge/pantry "what can I make" workflow
- Recommendations based on goals, likes, and dislikes
- Weekly spend tracking
- Direct ordering or checkout
- Native mobile app

## Success

The sprint succeeds if a user can paste a TikTok or reel link and receive, in a single flow, a grocery list, an approximate cost for the meal, per-meal macronutrients, and step-by-step cooking guidance. Success is defined as this end-to-end flow working reliably. Testing with real students and measuring whether it simplifies cooking for them is deferred beyond this sprint.

## Open questions or risks

Several questions remain open. The team has not yet chosen a source for grocery prices, and it is unclear how accurate cost estimates can be, since prices vary by store and location. The source for macronutrient data is also undecided. Ingredient extraction from a pasted link is a technical risk: some reels do not list ingredients in their captions or descriptions, and platform access may be restricted. The established alternatives identified (Samsung Food, Paprika, AnyList, Plan to Eat) still need to be verified. Finally, because testing with real students is deferred, the sprint will not show whether Breaking Bread actually simplifies cooking for beginners.
