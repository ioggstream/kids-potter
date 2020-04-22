import flask
from time import time as now
from random import randint, choices
from dataclasses import dataclass
import logging

log = logging.getLogger()


@dataclass
class User:
    name: str
    status: str = None
    last_spell: str = None
    ts: int = 0
    points: int = 500


flask.g = {"users": {}, "spells": {}}

all_spells = {
    "expelliarmus": {"type": "defence", "score": 0, "risk": 0, "time": 2},
    "expecto patronum": {"type": "defence", "score": 0, "risk": 0, "time": 5},
    "avada kedavra": {"type": "attack", "score": 25, "risk": 20, "time": 0},
    "incendio": {"type": "attack", "score": 15, "risk": 30, "time": 0},
    "petrificus": {"type": "attack", "score": 5, "risk": 0, "time": 3},
    "wingardium leviosa": {"type": "attack", "score": 40, "risk": 20, "time": 5},
}


def restart():
    spells = flask.g["spells"] = dict(choices(list(all_spells.items()), k=5))
    log.warning("spells: %r", spells)
    for username in flask.g["users"]:
        flask.g["users"][username] = User(name=username)


def post_restart():
    restart()


def get_user(username):
    return flask.g["users"].get(username, {})


def post_user(username):
    if username not in flask.g["users"]:
        flask.g["users"][username] = User(name=username)
    return flask.g["users"].get(username)


def post_cast(body, user=None, enemy=None):
    spells = flask.g["spells"]

    if enemy not in flask.g["users"]:
        return {"title": "nemico inesistente", "status": 404}
    enemy_u = flask.g["users"][enemy]

    if user not in flask.g["users"]:
        flask.g["users"][user] = User(name=user)
    user_u = flask.g["users"][user]

    if user_u.points <= 0:
        restart()

    spell = body.get("s", None)
    if spell not in spells:
        return {
            "title": f"non esiste questo incantesimo: {spell}",
            "status": 404,
            "body": body,
        }

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

    enemy_last_spell_effect = (
        spells[enemy_u.last_spell].get("time", 0) if enemy_u.last_spell in spells else 0
    )
    if enemy_u.status is "defence" and now() - enemy_u.ts < enemy_last_spell_effect:
        msg = f"{enemy} ha parato il tuo incantesimo"
        return {"game": flask.g, "data": body, "user": user, "title": msg}

    if enemy_u.status is "attack" and now() - enemy_u.ts < enemy_last_spell_effect:
        msg = f"{enemy} ti ha ancora bloccato"
        return {"game": flask.g, "data": body, "user": user, "title": msg}

    enemy_u.points -= my_spell["score"]

    if enemy_u.points <= 0:
        msg = "Hai vinto!"
        return {"game": flask.g, "data": body, "user": user, "title": msg}

    if my_spell["type"] == "defence":
        msg = "Difesa riuscita!"
    else:
        msg = "Bravo! L'hai colpito!"
    return {"game": flask.g, "data": body, "user": user, "title": msg}
