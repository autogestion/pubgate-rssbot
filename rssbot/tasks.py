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
        find_tag_scheme = r"(?!<a[^>]*?>)(?P<tagged>#\w+)(?![^<]*?</a>)"
        find_tag_scheme = re.compile(find_tag_scheme)

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
                            extra_tag_list = []
                            footer_tags = ""

                            content = entry.get("summary", None) or entry.get("content", None)[0]["value"]
                            if not (content and bot["details"]["rssbot"]["html"]):
                                content = entry['title']

                            # collect tags marked as "labels" in the post
                            if "tags" in entry:
                                extra_tag_list = [tag["term"] for tag in entry["tags"]]

                            # collect hardcoded tags from config
                            if bot["details"]["rssbot"]["tags"]:
                                extra_tag_list.extend(bot["details"]["rssbot"]["tags"])

                            # Make extra text list clickable
                            extra_tag_list = list(set(["#" + tag for tag in extra_tag_list]))
                            extra_tag_list_clickable = [f"<a href='' rel='tag'>{tag}</a>" for tag in extra_tag_list]

                            # collect tags from the post body
                            intext_tag_list = re.findall(find_tag_scheme, content)
                            if intext_tag_list:
                                content = re.sub(find_tag_scheme, r"<a href='' rel='tag'>\g<tagged></a>", content)

                            # Set tags as mastodon service info
                            apub_tag_list = set(intext_tag_list + extra_tag_list)
                            object_tags = [{
                                            "href": "",
                                            "name": tag,
                                            "type": "Hashtag"
                                           } for tag in apub_tag_list]

                            if extra_tag_list_clickable:
                                footer_tags = f"<br><br> {' '.join(extra_tag_list_clickable)}"

                            body = f"{content}{footer_tags}"

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
