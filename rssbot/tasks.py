import asyncio
import feedparser

from pubgate.db.models import User, Outbox
from pubgate.networking import fetch_text
from pubgate.activity import Note
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
                            "user_id": bot.name,
                            "feed_item_id": item["id"]
                        })
                        if exists:
                            continue
                        else:
                            content = item.get("summary", None) or item.get("content", None)[0]["value"]
                            if not (content and bot["details"]["rssbot"]["html"]):
                                content = item['title']

                            body_tags = ""
                            object_tags = []
                            if bot["details"]["rssbot"]["tags"]:
                                body_tags_list = []
                                for tag in bot["details"]["rssbot"]["tags"]:
                                    body_tags_list.append(
                                        f"<a href='' rel='tag'>#{tag}</a>"
                                    )
                                    object_tags.append({
                                        "href": "",
                                        "name": f"#{tag}",
                                        "type": "Hashtag"
                                    })

                                body_tags = f"<br><br> {' '.join(body_tags_list)}"

                            body = f"{content}{body_tags}"

                            activity = Note(bot, {
                                "type": "Create",
                                "object": {
                                    "type": "Note",
                                    "summary": None,
                                    "inReplyTo": "",
                                    "sensitive": False,
                                    "url": item['link'],
                                    "content": body,
                                    "tag": object_tags
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
                            recipients = await activity.recipients()

                            # post_to_remote_inbox
                            asyncio.ensure_future(deliver(activity.render, recipients))

                    await User.update_one(
                        {'name': bot.name},
                        {'$set': {"details.rssbot.feed_last_updated": feed_last_updated}}
                    )

            await asyncio.sleep(app.config.RSSBOT_TIMEOUT)
