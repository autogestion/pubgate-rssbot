
from sanic import response, Blueprint
from sanic_openapi import doc

from pubgate.db.models import User
from pubgate.api.auth import token_check


rssbot_bp = Blueprint('rssbot', url_prefix="rssbot")


@rssbot_bp.route('/<user>', methods=['PATCH'])
@doc.summary("Allow to disable/update rssbot")
@token_check
async def rssbot_update(request, user):

    await User.update_one(
        {'name': user.name},
        {'$set': {"details.rssbot": request.json}}
    )

    return response.json({'peremoga': 'yep'}, status=201)
