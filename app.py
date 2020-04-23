import flask
from time import time as now
from random import randint, choices
from dataclasses import dataclass
import logging
from connexion import problem

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
    "ta": {"type": "attack", "score": 1, "risk": 0, "time": 0},
    "td": {"type": "defence", "score": 1, "risk": 0, "time": 0},
    "expelliarmus": {"type": "defence", "score": 0, "risk": 0, "time": 2},
    "expecto patronum": {"type": "defence", "score": 0, "risk": 0, "time": 5},
    "avada kedavra": {"type": "attack", "score": 25, "risk": 20, "time": 0},
    "incendio": {"type": "attack", "score": 15, "risk": 30, "time": 0},
    "petrificus": {"type": "attack", "score": 5, "risk": 0, "time": 3},
    "wingardium leviosa": {"type": "attack", "score": 40, "risk": 20, "time": 5},
    "imperium": {"type": "attack", "score": 0, "risk": -50, "time": 10},
}


def restart(reduced_spells=False):
    flask.g["spells"] = all_spells  # ict(choices(list(all_spells.items()), k=5))
    for username in flask.g["users"]:
        flask.g["users"][username] = User(name=username)
    log.warning("status: %r", flask.g)
    return {"status": flask.g}


def post_restart():
    return restart()


def get_user(username):
    return flask.g["users"].get(username, {})


def post_user(username):
    if username not in flask.g["users"]:
        flask.g["users"][username] = User(name=username)
    return flask.g["users"].get(username)


def backfires(my_spell, enemy_spell):
    """
    :return True if my_spell backfires
    """
    if randint(0, 100) < my_spell["risk"]:
        return True

    if not enemy_spell:
        return False

    if enemy_spell["risk"] >= 0:
        return False

    if randint(0, 100) < -enemy_spell["risk"]:
        return True

    return False


def post_cast(body, user=None, enemy=None):
    spells = flask.g["spells"]

    enemy_u = flask.g["users"].get(enemy)
    user_u = flask.g["users"].get(user)

    if enemy_u is None:
        return problem(title="Not Found", detail="nemico inesistente", status=404)

    if user_u is None:
        return problem(title="Not Found", detail="giocatore inesistente", status=404)

    if user_u.points <= 0:
        msg = "Hai perso :("
        return {"game": flask.g, "data": body, "user": user, "title": msg}

    spell = body.get("s", None)
    if spell not in spells:
        return problem(
            title="Bad Request",
            detail=f"non esiste questo incantesimo: {spell}",
            status=400,
            ext=dict(body=body),
        )

    if spell == user_u.last_spell:
        msg = "non puoi usare un incantesimo due volte di seguito"
        return {"game": flask.g, "data": body, "user": user, "title": msg}

    # get active spells
    my_spell = spells[spell]
    enemy_spell = spells.get(enemy_u.last_spell, {})
    if now() - enemy_u.ts > enemy_spell.get("time", 0):
        enemy_spell = None

    user_u.last_spell = spell
    user_u.ts = now()
    user_u.status = my_spell["type"]

    if backfires(my_spell, enemy_spell):
        user_u.points -= my_spell["score"]
        msg = "L'incantesimo ti si è ritorto contro! Che sfortuna!"
        return {"game": flask.g, "data": body, "user": user, "title": msg}

    if enemy_u.status is "defence" and enemy_spell:
        msg = f"{enemy} ha parato il tuo incantesimo"
        return {"game": flask.g, "data": body, "user": user, "title": msg}

    if enemy_u.status is "attack" and enemy_spell:
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
