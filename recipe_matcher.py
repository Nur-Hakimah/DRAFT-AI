
import json
import re
from pathlib import Path

import pandas as pd


DATASET_PATH = (
    "/home/codespace/.cache/kagglehub/datasets/"
    "prashantsingh001/recipes-dataset-64k-dishes/"
    "versions/1/1_Recipe_csv.csv"
)


def parse_list(value):
    """Convert JSON-encoded ingredients or directions into a list."""
    if isinstance(value, list):
        return value

    if pd.isna(value):
        return []

    try:
        result = json.loads(value)
        return result if isinstance(result, list) else [str(result)]
    except (json.JSONDecodeError, TypeError):
        return [str(value)]


def normalize(text):
    """Normalize ingredient names for simple matching."""
    text = str(text).lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()



def load_recipes():
    """Load only the columns needed for recipe matching."""
    if not hasattr(load_recipes, "_cache"):
        df = pd.read_csv(
            DATASET_PATH,
            usecols=[
                "recipe_title",
                "ingredients",
                "directions",
            ],
        )
        df = df.drop_duplicates(subset=["recipe_title"])
        load_recipes._cache = df

    return load_recipes._cache


def find_matching_recipes(inventory, limit=5):
    """Find recipes that use ingredients in the user's inventory."""
    df = load_recipes()
    results = []

    inventory_names = [
        normalize(item["name"])
        for item in inventory
        if item.get("name")
    ]

    for _, row in df.iterrows():
        title = str(row.get("recipe_title", "")).strip()
        title_lower = title.lower()

        if any(word in title_lower for word in [
            "for dogs", "for cats", "dog treats", "cat treats"
        ]):
            continue

        ingredients = parse_list(row.get("ingredients", ""))
        directions = parse_list(row.get("directions", ""))

        matched = []
        missing = []


        used_inventory_names = set()

        for ingredient in ingredients:
            ingredient_text = str(ingredient).strip()
            ingredient_normalized = normalize(ingredient_text)
            ingredient_words = set(ingredient_normalized.split())

            found_name = None

            for name in inventory_names:
                if not name or name in used_inventory_names:
                    continue

                name_words = set(name.split())

                # Match whole words, including simple plurals.
                words_match = any(
                    word in ingredient_words
                    or (
                        word.endswith("s")
                        and word[:-1] in ingredient_words
                    )
                    for word in name_words
                )

                if words_match:
                    found_name = name
                    break

            if found_name:
                matched.append(ingredient_text)
                used_inventory_names.add(found_name)
            else:
                missing.append(ingredient_text)


        if not matched:
            continue

        total = len(ingredients)
        score = len(matched) / total if total else 0

        results.append({
            "title": title,
            "ingredients": ingredients,
            "directions": directions,
            "matched": matched,
            "missing": missing,
            "match_count": len(matched),
            "match_ratio": score,
        })

    results.sort(
        key=lambda recipe: (
            recipe["match_count"],
            recipe["match_ratio"],
        ),
        reverse=True,
    )

    return results[:limit]
