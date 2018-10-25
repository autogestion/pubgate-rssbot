__version__ = "0.1.2"

from rssbot.blueprints import rssbot_bp
from rssbot.tasks import rssbot_task

pg_blueprints = [rssbot_bp]
pg_tasks = [rssbot_task]
