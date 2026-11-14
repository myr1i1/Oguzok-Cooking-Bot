import asyncio
import os

from flask import Flask, abort, request

from bot import bot, dp

app = Flask(__name__)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

SECRET = os.getenv("WEBHOOK_SECRET")


@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != SECRET:
        abort(403)

    update = request.get_json()
    loop.run_until_complete(dp.feed_webhook_update(bot, update))
    return "ok"