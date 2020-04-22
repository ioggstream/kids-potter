import flask
from  time import time as now
from random import randint
from dataclasses import dataclass

@dataclass
class User:
    name: str
    status: str = None
    last_spell: str = None
    ts: int = 0
    points: int = 100


flask.g = {"users": {"harry": User(name="harry"), 'draco': User(name="draco")}}

spells = {
    "expelliamus": {"type": "attack", "score": 10, "risk": 0},
    "expecto patronum":  {"type": "defence", "score": 0, "risk": 0},
    "Avada Kedavra": {"type": "attack", "score": 25, "risk": 10}
}


def post_cast(body, user=None, enemy=None):

    if enemy not in flask.g['users']:
        return {"title": "nemico inesistente", "status": 404}
    enemy_u = flask.g['users'][enemy]

    if user not in flask.g['users']:
        flask.g['users'][user] = User(name=user)
    user_u = flask.g['users'][user]

    spell = body.get("s", None)
    if spell not in spells:
        return {"title": f"non esiste questo incantesimo: {spell}", "status": 404, "body": body}

    if spell == user_u.last_spell:
        msg = "non puoi usare un incantesimo due volte di seguito"
        return {"game": flask.g, "data": body, "user": user, "title": msg}

    my_spell = spells[spell]
    user_u.last_spell = spell
    user_u.ts = now()
    user_u.status = my_spell["type"]

    if randint(0, 100) < my_spell["risk"]:
        user_u.points -= my_spell["score"]
        msg = "L'incantesimo ti si è ritorto contro! Che sfortuna!"
        return {"game": flask.g, "data": body, "user": user, "title": msg}

    if enemy_u.status == "defence" and now() - enemy_u.ts < 5:
        msg = f"{enemy} ha parato il tuo incantesimo"
        return {"game": flask.g, "data": body, "user": user, "title": msg}

    enemy_u.points -= my_spell["score"]
    msg = "Bravo! L'hai colpito!"
    return {"game": flask.g, "data": body, "user": user, "title": msg}
