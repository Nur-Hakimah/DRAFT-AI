
import os
from datetime import date

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import get_connection, initialize_database
from recipe_matcher import find_matching_recipes

TOKEN = os.getenv("TELEBOT")

# Shared inventory for the current prototype.
# This matches the website's USER_ID in app.py.
USER_ID = "default"

RECIPES = [
    {
        "name": "Tomato Egg Stir-Fry",
        "ingredients": ["tomato", "egg"],
        "instructions": (
            "1. Cut tomatoes.\n"
            "2. Beat eggs.\n"
            "3. Cook them together."
        )
    },
    {
        "name": "Garlic Fried Rice",
        "ingredients": ["rice", "garlic", "egg"],
        "instructions": (
            "1. Fry garlic.\n"
            "2. Add rice.\n"
            "3. Add egg and stir-fry."
        )
    },
    {
        "name": "Banana Pancakes",
        "ingredients": ["banana", "egg", "flour"],
        "instructions": (
            "1. Mash banana.\n"
            "2. Mix with egg and flour.\n"
            "3. Cook in a pan."
        )
    },
]


def get_inventory():
    conn = get_connection()
    rows = conn.execute(
        """
       SELECT id, name, quantity, expiry_date, notified, last_reminded_days
        FROM ingredients
        WHERE user_id = ?
        ORDER BY expiry_date
        """,
        (USER_ID,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def start_reminder_check(context: ContextTypes.DEFAULT_TYPE):
    # Placeholder to keep reminder setup separate from database logic.
    pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.application.bot_data["chat_id"] = update.effective_chat.id
    await update.message.reply_text(
        "🍅 Welcome to CookMate AI!\n\n"
        "Send me ingredients for recipe ideas.\n\n"
        "Inventory commands:\n"
        "/add tomato | 2026-10-28\n"
        "/list - View your ingredients\n"
        "/reminders - Check items expiring within 3 days\n"
        "/help - Show commands"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.application.bot_data["chat_id"] = update.effective_chat.id
    print("DEBUG: /start received, chat_id =", update.effective_chat.id)

    await update.message.reply_text(
        "🍅 Welcome to CookMate AI!\n\n"
        "Send me ingredients for recipe ideas.\n\n"
        "Inventory commands:\n"
        "/add tomato | 2026-10-28\n"
        "/list - View your ingredients\n"
        "/reminders - Check items expiring within 3 days\n"
        "/help - Show commands"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🥕 CookMate AI Commands\n\n"
        "/add ingredient | YYYY-MM-DD\n"
        "Example: /add tomato | 2026-10-28\n\n"
        "/list - View shared inventory\n"
        "/reminders - Check upcoming expiry dates\n\n"
        "You can also send ingredients for recipe suggestions."
    )


async def add_ingredient(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    raw = " ".join(context.args)

    if "|" not in raw:
        await update.message.reply_text(
            "Use this format:\n/add tomato | 2026-10-28"
        )
        return

    name, expiry_text = [part.strip() for part in raw.split("|", 1)]

    if not name:
        await update.message.reply_text("Please enter an ingredient name.")
        return

    try:
        expiry = date.fromisoformat(expiry_text)
    except ValueError:
        await update.message.reply_text(
            "Invalid date. Use YYYY-MM-DD, e.g. 2026-10-28."
        )
        return

    if expiry < date.today():
        await update.message.reply_text(
            "That date is in the past. Check the date and try again."
        )
        return

    conn = get_connection()
    conn.execute(
        """
        INSERT INTO ingredients
        (user_id, name, quantity, expiry_date, notified)
        VALUES (?, ?, ?, ?, 0)
        """,
        (USER_ID, name, "Not specified", expiry.isoformat())
    )
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ Added {name}\nExpiry date: {expiry.isoformat()}\n"
        "This item is now in your shared CookMate AI inventory."
    )


async def list_ingredients(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    items = get_inventory()

    if not items:
        await update.message.reply_text(
            "Your inventory is empty. Try /add tomato | 2026-10-28"
        )
        return

    lines = ["🥕 Your Shared Kitchen Inventory:"]
    for index, item in enumerate(items, start=1):
        expiry = item["expiry_date"] or "No date"
        lines.append(
            f"{index}. {item['name']} — {item['quantity']} "
            f"— expires {expiry}"
        )

    await update.message.reply_text("\n".join(lines))



async def check_reminders(
    context: ContextTypes.DEFAULT_TYPE
):
    today = date.today()
    items = get_inventory()
    chat_id = context.application.bot_data.get("chat_id")
    print("DEBUG: check_reminders is running")
    print("DEBUG: chat_id =", chat_id)

    if not chat_id:
        return

    for item in items:
        if not item["expiry_date"]:
            continue

        try:
            expiry = date.fromisoformat(item["expiry_date"])
        except ValueError:
            continue

        days_left = (expiry - today).days

        # Send reminders only at these stages.
        if days_left not in (3, 1, 0):
            continue

        # Avoid sending the same reminder stage more than once.
        if item["last_reminded_days"] == days_left:
            continue

        if days_left == 3:
            urgency = "🟡 Expires in 3 days"
        elif days_left == 1:
            urgency = "🟠 Expires tomorrow"
        else:
            urgency = "🔴 Expires today"

        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"⏰ CookMate AI Expiry Reminder\n\n"
                    f"{urgency}\n"
                    f"Ingredient: {item['name']}\n"
                    f"Expiry date: {expiry.isoformat()}\n\n"
                    "Consider using it soon to reduce food waste!"
                )
            )

            conn = get_connection()
            conn.execute(
                """
                UPDATE ingredients
                SET notified = 1, last_reminded_days = ?
                WHERE id = ?
                """,
                (days_left, item["id"])
            )
            conn.commit()
            conn.close()

        except Exception as error:
            print(f"Could not send reminder: {error}")


async def reminders_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    items = get_inventory()
    today = date.today()
    upcoming = []

    # Remember the chat for scheduled reminder messages.
    context.application.bot_data["chat_id"] = update.effective_chat.id

    for item in items:
        if not item["expiry_date"]:
            continue

        try:
            days_left = (
                date.fromisoformat(item["expiry_date"]) - today
            ).days
        except ValueError:
            continue

        if 0 <= days_left <= 3:
            upcoming.append((item, days_left))

    upcoming.sort(key=lambda entry: entry[1])

    if not upcoming:
        await update.message.reply_text(
            "🌱 No ingredients expiring in the next 3 days."
        )
        return

    lines = ["⏰ Ingredients to use soon:"]
    for item, days_left in upcoming:
        lines.append(
            f"• {item['name']} — {days_left} day(s) remaining"
        )

    await update.message.reply_text("\n".join(lines))


async def remember_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat:
        context.application.bot_data["chat_id"] = update.effective_chat.id



async def recipes_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    items = get_inventory()
    today = date.today()

    if not items:
        await update.message.reply_text(
            "🥕 Your kitchen is empty!\n"
            "Use /add name | YYYY-MM-DD to add ingredients first."
        )
        return

    try:
        recipes = find_matching_recipes(items, limit=5)
    except Exception as error:
        print("Recipe matching error:", error)
        await update.message.reply_text(
            "Sorry, I couldn't load recipe ideas right now. "
            "Please try again later."
        )
        return

    if not recipes:
        await update.message.reply_text(
            "🍳 I couldn't find recipes using your ingredients yet. "
            "Try adding more ingredients with /add."
        )
        return

    inventory_names = {
        item["name"].strip().lower()
        for item in items
        if item.get("name")
    }

    results = []

    for recipe in recipes:
        expiring = []

        for item in items:
            name = item["name"].strip().lower()
            if name not in inventory_names or not item.get("expiry_date"):
                continue

            try:
                days_left = (
                    date.fromisoformat(item["expiry_date"]) - today
                ).days
            except ValueError:
                continue

            if 0 <= days_left <= 3:
                expiring.append(item["name"])

        results.append({
            "recipe": recipe,
            "expiring": sorted(set(expiring)),
        })

    results.sort(
        key=lambda result: (
            -len(result["expiring"]),
            -result["recipe"]["match_count"],
            -result["recipe"]["match_ratio"],
        )
    )

    lines = ["🍳 Recipe ideas from your kitchen:\n"]

    for result in results:
        recipe = result["recipe"]

        lines.append(f"🍽️ {recipe['title']}")
        lines.append(
            f"✅ Ingredients matched: "
            f"{recipe['match_count']}/{len(recipe['ingredients'])}"
        )

        if recipe["matched"]:
            lines.append(
                "🥕 Found in your inventory: "
                + ", ".join(recipe["matched"][:6])
            )

        if recipe["missing"]:
            lines.append(
                "🛒 You may need: "
                + ", ".join(recipe["missing"][:6])
            )

        if result["expiring"]:
            lines.append(
                "⏰ Use soon: "
                + ", ".join(result["expiring"])
            )

        directions = recipe.get("directions", [])
        if directions:
            lines.append("👩‍🍳 Instructions:")
            for index, step in enumerate(directions[:5], start=1):
                lines.append(f"{index}. {step}")

        lines.append("")

    message = "\n".join(lines)

    # Telegram messages have a length limit.
    await update.message.reply_text(message[:4000])

async def find_recipe(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.message.text.lower()
    matches = []

    for recipe in RECIPES:
        found = [
            ingredient for ingredient in recipe["ingredients"]
            if ingredient in message
        ]
        if found:
            matches.append((recipe, found))

    if not matches:
        await update.message.reply_text(
            "🤔 No matching recipe yet. Try tomato, egg, rice, "
            "garlic, banana or flour."
        )
        return

    for recipe, found in matches:
        missing = [
            ingredient for ingredient in recipe["ingredients"]
            if ingredient not in found
        ]

        await update.message.reply_text(
            f"🍳 {recipe['name']}\n\n"
            f"Matched: {', '.join(found)}\n"
            f"{recipe['instructions']}\n\n"
            f"Still need: {', '.join(missing) if missing else 'None listed!'}"
        )


def main():
    if not TOKEN:
        raise RuntimeError("TELEBOT environment variable is missing.")

    initialize_database()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add", add_ingredient))
    app.add_handler(CommandHandler("list", list_ingredients))
    app.add_handler(CommandHandler("reminders", reminders_command))
    app.add_handler(CommandHandler("recipes", recipes_command))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, find_recipe)
    )

    # Remember the chat whenever a normal message is received.
    app.add_handler(
        MessageHandler(filters.TEXT, remember_chat),
        group=1
    )


    # Check expiry dates every hour while the bot is running.
    app.job_queue.run_repeating(
        check_reminders,
        interval=3600,
        first=2
    )

    print("CookMate AI Telegram bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
