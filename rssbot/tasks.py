import asyncio
import time

import aiohttp
import feedparser
from sanic.log import logger
from sanic import Blueprint

from pubgate.db import Outbox, User
from pubgate.utils.networking import fetch_text
from pubgate.activity import Create

from rssbot.utils import process_tags, move_image_to_attachment

bot_tasks = Blueprint("bot_tasks")


@bot_tasks.listener("after_server_start")
async def runbot(app, loop):
    while True:
        active_bots = await User.find(filter={"details.rssbot.enable": True})
        for bot in active_bots.objects:
            try:
                feed = await fetch_text(bot["details"]["rssbot"]["feed"])
            except aiohttp.client_exceptions.ClientConnectorError as e:
                logger.error(e)
                continue

            parsed_feed = feedparser.parse(feed)
            last_updated = bot["details"]["rssbot"].get('feed_last_updated', None)
            feed_last_updated = parsed_feed["feed"].get("updated", None)

            if last_updated and last_updated == feed_last_updated:
                continue
            else:
                for entry in parsed_feed["entries"]:
                    exists = await Outbox.find_one({
                        "user_id": bot.name,
                        "feed_item_id": entry["id"]
                    })
                    if exists:
                        continue
                    else:
                        content = entry.get("summary", None) or entry.get("content", None)[0]["value"]
                        if not (content and bot["details"]["rssbot"]["html"]):
                            content = entry['title']

                        # process tags
                        content, footer_tags, object_tags = process_tags(entry, content, bot)

                        # move images to attachments
                        attachment_object = []
                        if app.config.MOVE_IMG_TO_ATTACHMENT:
                            content = move_image_to_attachment(content, attachment_object)

                        body = f"{content}{footer_tags}"
                        published = time.strftime('%Y-%m-%dT%H:%M:%SZ', entry["published_parsed"])

                        activity = Create(bot, {
                            "type": "Create",
                            "cc": [],
                            "published": published,
                            "object": {
                                "type": "Note",
                                "summary": None,
                                "sensitive": False,
                                "url": entry['link'],
                                "content": body,
                                "published": published,
                                "attachment": attachment_object,
                                "tag": object_tags
                            }
                        })
                        await activity.save(feed_item_id=entry["id"])
                        await activity.deliver()
                        logger.info(f"rss entry '{entry['title']}' of {bot.name} federating")

                        if app.config.POSTING_TIMEOUT:
                            await asyncio.sleep(app.config.RSSBOT_TIMEOUT)

                await User.update_one(
                    {'name': bot.name},
                    {'$set': {"details.rssbot.feed_last_updated": feed_last_updated}}
                )

        await asyncio.sleep(app.config.RSSBOT_TIMEOUT)
