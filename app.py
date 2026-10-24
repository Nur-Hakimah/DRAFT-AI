
import streamlit as st
from datetime import date

st.set_page_config(
    page_title="CookMate AI",
    page_icon="🍅",
    layout="wide"
)

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

if "ingredients" not in st.session_state:
    st.session_state.ingredients = []

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
                st.session_state.ingredients.append({
                    "name": ingredient_name.strip(),
                    "quantity": quantity.strip() or "Not specified",
                    "expiry": expiry_date
                })
                st.success(f"Added {ingredient_name.strip()}!")
            else:
                st.warning("Please enter an ingredient name.")

    st.divider()
    st.subheader("Your ingredients")

    if not st.session_state.ingredients:
        st.info("Your kitchen is empty. Add your first ingredient above!")
    else:
        for i, item in enumerate(st.session_state.ingredients):
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

                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.ingredients.pop(i)
                    st.rerun()

with recipe_tab:
    st.subheader("Find recipes from your ingredients")
    st.write("Select ingredients you want to cook with.")

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

    available = [
        item["name"].lower()
        for item in st.session_state.ingredients
    ]

    if st.button("✨ Find matching recipes"):
        matches = []

        for recipe in recipes:
            matched = [
                ingredient
                for ingredient in recipe["ingredients"]
                if any(ingredient in name for name in available)
            ]

            if matched:
                matches.append((recipe, matched))

        if matches:
            for recipe, matched in matches:
                with st.container(border=True):
                    st.markdown(f"### 🍽️ {recipe['name']}")
                    st.write(recipe["description"])
                    st.write("Ingredients you have: " + ", ".join(matched))
                    missing = [
                        ingredient
                        for ingredient in recipe["ingredients"]
                        if ingredient not in matched
                    ]
                    st.write(
                        "You may still need: " + ", ".join(missing)
                        if missing else "You have the listed ingredients!"
                    )
        else:
            st.info(
                "No matches yet. Add ingredients such as tomato, egg, "
                "rice, garlic, chicken, carrot, broccoli, banana or flour."
            )

with waste_tab:
    st.subheader("Food Waste Tracker 🌱")

    ingredients = st.session_state.ingredients
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

