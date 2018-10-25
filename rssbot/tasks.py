import asyncio
import feedparser

from pubgate.db.models import User, Outbox
from pubgate.networking import fetch_text
from pubgate.renders import Activity
from pubgate.utils import make_label
from pubgate.networking import deliver


def rssbot_task(app):
    print("rssbot_task register")

    @app.listener("after_server_start")
    async def runbot(app, loop):
        while True:
            active_bots = await User.find(filter={"details.rssbot.enable": True})
            for bot in active_bots.objects:
                feed = await fetch_text(bot["details"]["rssbot"]["feed"])
                parsed_feed = feedparser.parse(feed)
                last_updated = bot["details"]["rssbot"].get('feed_last_updated', None)
                feed_last_updated = parsed_feed["feed"].get("updated", None)

                if last_updated and last_updated == feed_last_updated:
                    continue
                else:
                    for item in parsed_feed["entries"]:
                        exists = await Outbox.find_one({
                            "user_id": bot["username"],
                            "feed_item_id": item["id"]
                        })
                        if exists:
                            continue
                        else:
                            content = item.get("content", None)
                            if content and bot["details"]["rssbot"]["html"]:
                                content = content[0]["value"]
                            else: content = item['title']

                            tags = [f"#{x}" if not x.startswith("#") else x for x in bot["details"]["rssbot"]["tags"]]
                            body = f"{content} \n {item['link']} \n {' '.join(tags)} "

                            activity = Activity(bot.name, {
                                "type": "Create",
                                "object": {
                                    "type": "Note",
                                    "summary": None,
                                    "inReplyTo": "",
                                    "to": [
                                        "https://www.w3.org/ns/activitystreams#Public"
                                    ],
                                    "sensitive": False,
                                    "content": body,
                                }
                            })
                            await Outbox.insert_one({
                                "_id": activity.id,
                                "user_id": bot.name,
                                "activity": activity.render,
                                "label": make_label(activity.render),
                                "meta": {"undo": False, "deleted": False},
                                "feed_item_id": item["id"]
                            })
                            recipients = await bot.followers_get()

                            # post_to_remote_inbox
                            asyncio.ensure_future(deliver(activity.render, recipients))

                    await User.update_one(
                        {'name': bot.name},
                        {'$set': {"details.rssbot.feed_last_updated": feed_last_updated}}
                    )

            await asyncio.sleep(app.config.RSSBOT_TIMEOUT)
