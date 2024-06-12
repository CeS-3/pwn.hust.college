import datetime

from CTFd.cache import cache
from flask import url_for
from ..models import Dojos, Belts


BELT_REQUIREMENTS = {
    "orange": "intro-to-cybersecurity",
    "yellow": "program-security",
    "green": "system-security",
    "blue": "software-exploitation",
}

def belt_asset(color):
    belt = color + ".svg" if color in BELT_REQUIREMENTS else "white.svg"
    return url_for("views.themes", path=f"img/dojo/{belt}")

def get_user_belts(user):
    result = [ ]
    for belt, dojo_id in BELT_REQUIREMENTS.items():
        dojo = Dojos.query.filter(Dojos.official, Dojos.id == dojo_id).first()
        if not dojo:
            # We are likely missing the correct dojos in the DB (e.g., custom deployment)
            break
        if not dojo.completed(user):
            break
        result.append(belt)
    return result

@cache.memoize(timeout=60)
def get_belts():
    result = {
        "dates": {},
        "users": {},
        "ranks": {},
    }

    for n,(color,dojo_id) in enumerate(BELT_REQUIREMENTS.items()):
        dojo = Dojos.query.filter_by(id=dojo_id).first()
        if not dojo:
            # We are likely missing the correct dojos in the DB (e.g., custom deployment)
            break

        result["dates"][color] = {}
        result["ranks"][color] = []

        for belt in Belts.query.filter_by(name=color).order_by(Belts.date):
            result["dates"][color][belt.user.id] = str(belt.date)
            result["users"][belt.user.id] = {
                "handle": belt.user.name,
                "site": belt.user.website,
                "color": color,
                "date": str(belt.date),
                "rank_id": n,
            }

    for user_id in result["users"]:
        result["ranks"][result["users"][user_id]["color"]].append(user_id)

    return result
