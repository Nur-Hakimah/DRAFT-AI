
from recipe_matcher import find_matching_recipes

# Simulate ingredients in CookMate inventory
inventory = [
    {"name": "potato"},
    {"name": "ketchup"},
    {"name": "garlic"},
]

recipes = find_matching_recipes(inventory, limit=5)

for recipe in recipes:
    print(f"\n🍳 {recipe['title']}")
    print(f"✅ Available: {', '.join(recipe['matched']) or 'None'}")
    print(f"🛒 Missing: {', '.join(recipe['missing']) or 'None'}")
    print(f"📊 Match score: {recipe['match_ratio']:.0%}")
