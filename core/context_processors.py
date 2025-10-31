from typing import Optional

from django.http import HttpRequest

from .models import Contestant
from .views import SESSION_AUTH_USER_ID


def current_contestant(request: HttpRequest):
    contestant: Optional[Contestant] = None
    contestant_id = request.session.get(SESSION_AUTH_USER_ID)
    if contestant_id:
        try:
            contestant = Contestant.objects.get(id=contestant_id)
        except Contestant.DoesNotExist:
            contestant = None
    return {"current_contestant": contestant}
