
import streamlit as st
from datetime import date
from database import get_connection, initialize_database

st.set_page_config(
    page_title="CookMate AI",
    page_icon="🍅",
    layout="wide"
)
st.link_button(
    "💬 Chat with CookMate AI on Telegram",
    "https://t.me/CookMateAI123_bot"
)

# Initialise the database
initialize_database()

# Temporary shared ID for this single-user prototype.
# We will connect Telegram to this same inventory in the next step.
USER_ID = "default"

st.markdown("""
<style>
.stApp {
    background: #FFF5E9;
    color: #4A2F24;
}
.block-container {
    padding-top: 2rem;
    max-width: 1100px;
}
h1, h2, h3 {
    color: #B9382A;
}
[data-testid="stSidebar"] {
    background-color: #F4D5B8;
}
.stButton > button {
    background-color: #B9382A;
    color: white;
    border: none;
    border-radius: 10px;
}
.stButton > button:hover {
    background-color: #E87932;
    color: white;
}
</style>
""", unsafe_allow_html=True)


def get_ingredients():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, name, quantity, expiry_date
        FROM ingredients
        WHERE user_id = ?
        ORDER BY expiry_date
        """,
        (USER_ID,)
    ).fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "quantity": row["quantity"],
            "expiry": date.fromisoformat(row["expiry_date"])
            if row["expiry_date"] else date.today()
        }
        for row in rows
    ]


def add_ingredient(name, quantity, expiry):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO ingredients
        (user_id, name, quantity, expiry_date)
        VALUES (?, ?, ?, ?)
        """,
        (USER_ID, name, quantity, expiry.isoformat())
    )
    conn.commit()
    conn.close()


def remove_ingredient(ingredient_id):
    conn = get_connection()
    conn.execute(
        "DELETE FROM ingredients WHERE id = ? AND user_id = ?",
        (ingredient_id, USER_ID)
    )
    conn.commit()
    conn.close()


st.title("🍅 CookMate AI")
st.write("**Your kitchen, made smarter.**")
st.write(
    "Use what you have, discover delicious recipes, "
    "and reduce food waste."
)

st.divider()

inventory_tab, recipe_tab, waste_tab = st.tabs([
    "🥕 My Kitchen",
    "🍳 Recipe Finder",
    "🌱 Food Waste Tracker"
])

with inventory_tab:
    st.subheader("What's in your kitchen?")
    st.caption("Add ingredients and keep an eye on their expiry dates.")

    with st.form("ingredient_form", clear_on_submit=True):
        ingredient_name = st.text_input(
            "Ingredient name",
            placeholder="e.g. Eggs, tomatoes, chicken"
        )
        quantity = st.text_input(
            "Quantity",
            placeholder="e.g. 6 eggs, 200 g"
        )
        expiry_date = st.date_input(
            "Expiry date",
            value=date.today()
        )
        submitted = st.form_submit_button("＋ Add ingredient")

        if submitted:
            if ingredient_name.strip():
                add_ingredient(
                    ingredient_name.strip(),
                    quantity.strip() or "Not specified",
                    expiry_date
                )
                st.success(f"Added {ingredient_name.strip()}!")
                st.rerun()
            else:
                st.warning("Please enter an ingredient name.")

    st.divider()
    st.subheader("Your ingredients")

    ingredients = get_ingredients()

    if not ingredients:
        st.info("Your kitchen is empty. Add your first ingredient above!")
    else:
        for item in ingredients:
            days_left = (item["expiry"] - date.today()).days

            if days_left < 0:
                status = "🔴 Past expiry date"
            elif days_left <= 3:
                status = "🟠 Use soon"
            else:
                status = "🟢 Fresh for now"

            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 2])

                col1.markdown(f"**{item['name']}**")
                col1.caption(item["quantity"])
                col2.write(f"Expiry: {item['expiry']}")
                col3.write(status)

                if st.button("Remove", key=f"remove_{item['id']}"):
                    remove_ingredient(item["id"])
                    st.rerun()


with recipe_tab:
    st.subheader("Find recipes from your ingredients")
    st.write(
        "CookMate AI matches recipes to your inventory "
        "and prioritises ingredients that are expiring soon."
    )

    recipes = [
        {
            "name": "Tomato Egg Stir-Fry",
            "ingredients": ["tomato", "egg"],
            "description": "A simple, comforting tomato and egg dish."
        },
        {
            "name": "Garlic Fried Rice",
            "ingredients": ["rice", "garlic", "egg"],
            "description": "An easy way to use leftover rice."
        },
        {
            "name": "Chicken Vegetable Stir-Fry",
            "ingredients": ["chicken", "carrot", "broccoli"],
            "description": "A colourful meal with protein and vegetables."
        },
        {
            "name": "Banana Pancakes",
            "ingredients": ["banana", "egg", "flour"],
            "description": "A sweet option for ripe bananas."
        }
    ]

    if st.button("✨ Find matching recipes"):
        inventory = get_ingredients()

        if not inventory:
            st.info("Add ingredients to My Kitchen first.")
        else:
            today = date.today()
            available_names = {
                item["name"].lower()
                for item in inventory
            }

            # Find ingredients that are approaching expiry.
            expiring_names = {
                item["name"].lower()
                for item in inventory
                if 0 <= (item["expiry"] - today).days <= 3
            }

            results = []

            for recipe in recipes:
                matched = [
                    ingredient
                    for ingredient in recipe["ingredients"]
                    if any(
                        ingredient in name
                        for name in available_names
                    )
                ]

                if not matched:
                    continue

                missing = [
                    ingredient
                    for ingredient in recipe["ingredients"]
                    if ingredient not in matched
                ]

                # Match expiring inventory items to recipe ingredients.
                expiring_matched = [
                    ingredient
                    for ingredient in matched
                    if any(
                        ingredient in name
                        for name in expiring_names
                    )
                ]

                match_score = len(matched) / len(recipe["ingredients"])
                waste_score = len(expiring_matched)

                results.append({
                    "recipe": recipe,
                    "matched": matched,
                    "missing": missing,
                    "expiring_matched": expiring_matched,
                    "match_score": match_score,
                    "waste_score": waste_score
                })

            # Rank recipes by expiring ingredients first,
            # then by ingredient match percentage.
            results.sort(
                key=lambda result: (
                    result["waste_score"],
                    result["match_score"]
                ),
                reverse=True
            )

            if not results:
                st.info(
                    "No matching recipes yet. Try adding tomato, egg, "
                    "rice, garlic, chicken, carrot, broccoli, banana or flour."
                )
            else:
                for result in results:
                    recipe = result["recipe"]

                    with st.container(border=True):
                        st.markdown(f"### 🍽️ {recipe['name']}")
                        st.write(recipe["description"])

                        st.progress(result["match_score"])
                        st.caption(
                            f"Ingredient match: "
                            f"{result['match_score']:.0%}"
                        )

                        st.write(
                            "**Ingredients you have:** "
                            + ", ".join(result["matched"])
                        )

                        if result["expiring_matched"]:
                            st.warning(
                                "🌱 Helps use ingredients expiring soon: "
                                + ", ".join(result["expiring_matched"])
                            )
                        else:
                            st.write(
                                "🌱 No soon-to-expire ingredient matched."
                            )

                        if result["missing"]:
                            st.write(
                                "**You may still need:** "
                                + ", ".join(result["missing"])
                            )
                        else:
                            st.success(
                                "You have all the listed recipe ingredients!"
                            )

with waste_tab:
    st.subheader("Food Waste Tracker 🌱")

    ingredients = get_ingredients()

    expiring = [
        item for item in ingredients
        if 0 <= (item["expiry"] - date.today()).days <= 3
    ]
    expired = [
        item for item in ingredients
        if (item["expiry"] - date.today()).days < 0
    ]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total ingredients", len(ingredients))
    col2.metric("Use within 3 days", len(expiring))
    col3.metric("Past expiry date", len(expired))

    if expiring:
        st.warning("Consider using these ingredients soon:")
        for item in expiring:
            st.write(f"- {item['name']} — expires {item['expiry']}")
    else:
        st.success("No ingredients are approaching their expiry date!")

    if expired:
        st.caption(
            "Check the condition and food-safety guidance for expired "
            "items before deciding whether they are safe to consume."
        )

st.divider()
st.caption("CookMate AI • Draft prototype • Less waste, more taste.")
