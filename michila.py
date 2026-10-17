
from collections import deque

from telegram import Update, ReactionTypeEmoji
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = ""
CHANNEL = ""
OWNER_ID = ""

# Store the five most recent posts received while running.
recent_posts = deque(maxlen=5)


async def save_post(update, context):
    post = update.channel_post

    if post and post.chat.id == CHANNEL:
        recent_posts.append({
            "id": post.message_id,
            "text": post.text or post.caption or "[No text]",
        })


async def show_posts(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_user.id != OWNER_ID:
        return

    if not recent_posts:
        await update.message.reply_text(
            "No posts collected yet. Publish a new channel post first."
        )
        return

    lines = ["Latest collected channel posts:\n"]

    for post in reversed(recent_posts):
        lines.append(
            f"ID: {post['id']}\n{post['text'][:200]}\n"
        )

    await update.message.reply_text("\n".join(lines))


async def like_post(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_user.id != OWNER_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /like MESSAGE_ID [EMOJI]"
        )
        return

    try:
        message_id = int(context.args[0])
        emoji = context.args[1] if len(context.args) > 1 else "❤️"

        await context.bot.set_message_reaction(
            chat_id=CHANNEL,
            message_id=message_id,
            reaction=[ReactionTypeEmoji(emoji=emoji)],
        )

        await update.message.reply_text(
            f"Reaction {emoji} added to post {message_id}."
        )

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


app = Application.builder().token(BOT_TOKEN).build()

# Collect new channel posts.
app.add_handler(
    MessageHandler(filters.UpdateType.CHANNEL_POST, save_post)
)

# Commands you can use in the bot's private chat.
app.add_handler(CommandHandler("posts", show_posts))
app.add_handler(CommandHandler("like", like_post))

app.run_polling()
