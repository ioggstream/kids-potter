from collections import defaultdict

import flask
from time import time as now
from random import randint, choices
from dataclasses import dataclass
import logging, yaml
from connexion import problem
from pathlib import Path
import json, dataclasses
import editdistance

logging.basicConfig(filename="server.log", level=logging.DEBUG)
log = logging.getLogger()

HANDICAP_USERS = ("python",)


class DataclassJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


from flask import current_app as app


@dataclass
class User:
    name: str
    status: str = None
    last_spell: str = None
    ts: int = 0
    points: int = 100
    level: int = 0
    stats: dict = None

    def __post_init__(self):
        self.stats = {"spells": {"errors": 0, "typespeed": {"last": 0, "average": 0}}}
        if self.name in HANDICAP_USERS:
            self.level = -1
            self.points = 50


@dataclass
class Spell:
    name: str
    type: str
    score: int = 0
    time: int = 0
    risk: int = 0
    description: str = None
    level: int = 0
    on_insufficient_level: str = "Non hai ancora imparato questo incantesimo!"
    score_level: int = 0


flask.g = {"users": {"a": User(name="a"), "b": User(name="b")}, "spells": {}}


def load_spells():
    return {
        s["name"]: Spell(**s)
        for s in yaml.safe_load(Path("spells.yml").read_text())["spells"]
    }


def restart(reduced_spells=False):
    flask.g["spells"] = load_spells()  # ict(choices(list(all_spells.items()), k=5))
    for username in flask.g["users"]:
        flask.g["users"][username] = User(name=username)
    log.warning("status: %r", flask.g)
    return {"status": flask.g}


def get_status():
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
    if randint(0, 100) < my_spell.risk:
        return True

    if not enemy_spell:
        return False

    if enemy_spell.risk >= 0:
        return False

    if randint(0, 100) < -enemy_spell.risk:
        return True

    return False


def _update_stats(user_u, spell):
    q = 0.92
    # update stats
    if spell not in flask.g["spells"]:
        user_u.stats["spells"]["errors"] += 1
        return

    spell_stats = user_u.stats["spells"]
    if spell not in spell_stats:
        spell_stats[spell] = 1
    spell_stats[spell] += 1
    spell_stats["typespeed"]["last"] = current_typespeed = (
        int(now() - user_u.ts) if user_u.ts else 0
    )

    spell_stats["typespeed"]["average"] = int(
        q * spell_stats["typespeed"]["average"] + (1 - q) * current_typespeed
        if spell_stats["typespeed"]["average"]
        else current_typespeed
    )


SPELL_OK, SPELL_KO, SPELL_MISSING = range(3)


def _misspelt(spell, spells):
    """
    Returns None if the spell is correct or not existing. Otherwise returns the
    misspelt spell.
    :param spell:
    :param spells:
    :return:
    """
    from phonetics import metaphone
    from editdistance import eval as edit_distance

    assert spell
    log.debug("Looking for %r in %r", spell, spells)
    if spell in spells:
        return (spell, SPELL_OK)

    phonetic_spell = metaphone(spell)[:5]
    for existing_spell in spells:
        if edit_distance(metaphone(existing_spell)[:5], phonetic_spell) <= 2:
            log.warning("Incantesimo scorretto: %r invece di %r", spell, existing_spell)
            return (existing_spell, SPELL_KO)

    return (spell, SPELL_MISSING)


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
    log.warning(f"{user}, {enemy}, {spell}")
    _update_stats(user_u, spell)

    spell, misspelt = _misspelt(spell, spells)
    if misspelt == SPELL_MISSING:
        log.warning("Incantesimo inesistente: %r", spell)
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
    enemy_spell = spells.get(enemy_u.last_spell, None)

    # Check spell level.
    if 0 <= user_u.level < my_spell.level:
        msg = f"{my_spell.on_insufficient_level}"
        return {"game": flask.g, "data": body, "user": user, "title": msg}

    # Expire the enemy spell.
    log.warning("Enemy spell: %r cast %r", enemy_spell, now() - enemy_u.ts)
    if now() - enemy_u.ts > enemy_spell.time if enemy_spell else 0:
        enemy_spell = None

    # Update user properties.
    # If you misspell a spell, you can't retry it
    # as it will be your active spell.
    user_u.last_spell = spell
    # If the spell is correct, update timestamp and status.
    if misspelt == SPELL_OK:
        user_u.ts = now()
        user_u.status = my_spell.type

    # The spell backfires if misspelt or because of risk
    if misspelt == SPELL_KO or backfires(my_spell, enemy_spell):
        user_u.points -= my_spell.score
        msg = f'L\'incantesimo "{spell}" ti si è ritorto contro! Che sfortuna!'
        return {"game": flask.g, "data": body, "user": user, "title": msg}

    log.warning("Enemy status %r, spell %r", enemy_u.status, enemy_spell)
    if enemy_u.status == "defence" and enemy_spell:
        msg = f"{enemy} ha parato il tuo incantesimo"
        return {"game": flask.g, "data": body, "user": user, "title": msg}

    if enemy_u.status == "attack" and enemy_spell:
        msg = f"{enemy} ti ha ancora bloccato"
        return {"game": flask.g, "data": body, "user": user, "title": msg}

    # Consider handicap
    handicap_factor = 1
    if user_u.level < 0 and enemy_u.stats["spells"]["typespeed"]["average"]:
        handicap_factor = (
            user_u.stats["spells"]["typespeed"]["average"]
            / enemy_u.stats["spells"]["typespeed"]["average"]
        )
        log.warning("Reducing spell attack of %r", handicap_factor)
    else:
        user_u.level += bool(my_spell.score)

    damage = my_spell.score + user_u.level * my_spell.score_level
    enemy_u.points -= int(damage * min(handicap_factor, 1))

    if enemy_u.points <= 0:
        msg = "Hai vinto!"
        return {"game": flask.g, "data": body, "user": user, "title": msg}

    if my_spell.type == "defence":
        msg = "Difesa riuscita!"
    else:
        msg = "Bravo! L'hai colpito!"
    return {"game": flask.g, "data": body, "user": user, "title": msg}
