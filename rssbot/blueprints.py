
from sanic import response, Blueprint
from sanic_openapi import doc

from pubgate.api.v1.db.models import User
from pubgate.api.v1.views.auth import auth_required


rssbot_bp = Blueprint('rssbot', url_prefix="rssbot")


@rssbot_bp.route('/<user_id>', methods=['PATCH'])
@doc.summary("Allow to disable/update rssbot")
@auth_required
async def rssbot_update(request, user_id):
    user = await User.find_one(dict(username=user_id))
    if not user:
        return response.json({"zrada": "no such user"}, status=404)

    await User.update_one(
        {'username': user_id},
        {'$set': {"details.rssbot": request.json}}
    )

    return response.json({'peremoga': 'yep'}, status=201)
