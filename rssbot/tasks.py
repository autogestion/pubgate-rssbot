import asyncio
import re

import aiohttp
import feedparser
from sanic.log import logger

from pubgate.db.models import Outbox
from pubgate.db.user import User
from pubgate.utils.networking import fetch_text
from pubgate.activity import Create


def rssbot_task(app):
    logger.info("rssbot_task registered")

    @app.listener("after_server_start")
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
                            body_tags = ""
                            object_tags = []
                            body_tags_list = []
                            tag_list = []

                            content = entry.get("summary", None) or entry.get("content", None)[0]["value"]
                            if not (content and bot["details"]["rssbot"]["html"]):
                                content = entry['title']

                            find_tag_scheme = r"(?!<a[^>]*?>)(?P<tagged>#\w+)(?![^<]*?</a>)"
                            find_tag_scheme = re.compile(find_tag_scheme)
                            text_tags = re.findall(find_tag_scheme, content)
                            if text_tags:
                                for tag in text_tags:
                                    addtag(tag, body_tags_list, object_tags)
                                content = re.sub(find_tag_scheme, r"<a href='' rel='tag'>'\g<tagged>'</a>", content)

                            if "tags" in entry:
                                for tag in entry["tags"]:
                                    tag_name = tag["term"]
                                    addtag(tag_name, body_tags_list, object_tags, add_octothorpe=True)

                            if bot["details"]["rssbot"]["tags"]:
                                for tag in bot["details"]["rssbot"]["tags"]:
                                    addtag(tag, body_tags_list, object_tags, add_octothorpe=True)

                                body_tags = f"<br><br> {' '.join(body_tags_list)}"

                            body = f"{content}{body_tags}"

                            activity = Create(bot, {
                                "type": "Create",
                                "cc": [],
                                "object": {
                                    "type": "Note",
                                    "summary": None,
                                    "inReplyTo": "",
                                    "sensitive": False,
                                    "url": entry['link'],
                                    "content": body,
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

    def addtag(tag_name, tag_text_list, tag_object, add_octothorpe=False):
        if add_octothorpe:
            name_pattern = f"#{tag_name}"
        else:
            name_pattern = f"{tag_name}"

        tag_text_pattern = f"<a href='' rel='tag'>{name_pattern}</a>"
        tag_object_pattern = {
            "href": "",
            "name": name_pattern,
            "type": "Hashtag"
        }

        if tag_text_pattern not in tag_text_list:
            tag_text_list.append(tag_text_pattern)

        if tag_object_pattern not in tag_object:
            tag_object.append(tag_object_pattern)

