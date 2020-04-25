from random import randint, choice

from requests import post, get, exceptions
import json

from sys import argv
from pathlib import Path
from threading import Thread
from time import sleep

DEFENCE_ICON = "🛡"
ATTACK_ICON = "━━━★"


def iconize(s):
    tr_map = {"defence": DEFENCE_ICON, "attack": ATTACK_ICON}
    for k, v in tr_map.items():
        s = s.replace(k, v)
    return s


def play_music():
    try:
        from pygame import mixer
        import pygame

        mixer.pre_init(44100, -16, 2, 2048)
        mixer.init()
        audio = Path("audio.mp3")
        if not audio.is_file():
            # download content from archive.org
            u = "https://archive.org/serve/11TheQuidditchMatch/2001%20-%20Harry%20Potter%20and%20The%20Sorcerer%27s%20Stone%2F01%20-%20Prologue.mp3"
            r = get(u)
            audio.write_bytes(r.content)
        mixer.music.load(audio.name)
        mixer.music.play(0)
    except (ImportError, pygame.error):
        pass


def _input_server(default_server):
    has_server = None

    while not has_server:
        server = (
            input(f"Inserisci l'indirizzo del server [{default_server}]: ")
            or default_server
        )
        url = f"http://{server}" if not server.startswith("http") else server
        try:
            has_server = get(f"{url}/status")
        except exceptions.ConnectionError:
            print(f"Il server {url} non è raggiungibile. Riprova più tardi.")

    return url


def _input_enemy(url):
    has_enemy = None
    while not has_enemy:
        enemy_name = input("Chi è il tuo avversario [draco]? ") or "draco"
        has_enemy = get(f"{url}/user/{enemy_name}").json()
        if not has_enemy:
            print("Il nemico non si è ancora unito al gioco")
        else:
            print(has_enemy)
    return enemy_name


def _command(url, spell):
    if spell.startswith("/"):
        print(get(f"{url}/{spell}").content)
    elif spell.startswith("+/"):
        spell = spell[1:]
        print(post(f"{url}/{spell}").content)
    else:
        return False

    return True

import click


@click.command()
@click.option('--server', default="http://localhost:5000", help='Server address.')
@click.option('--music/--no-music', default=True,
              help='Play background music.')
@click.option('--player', prompt='Come ti chiami?', default="harry")
@click.option('--computer', prompt='Giocatore computer?', default=False)
def main(server, music, player, computer):
    t = Thread(target=play_music)
    if music:
        t.start()
    game(server, player, not computer)
    if music:
        t.join()


def game(server, player, human):
    print("\n\n\nWelcome to Pòno Pòtter\n\n\n")
    sleep(1)

    url = _input_server(server)
    user = post(f"{url}/user/{player}").json()
    user_name = user["name"]
    enemy_name = _input_enemy(url)
    server_status = post(f"{url}/restart").json()["status"]
    all_spells = list(server_status["spells"].keys())

    while True:
        # Read spell
        if human:
            spell = input(
                iconize(f"{user_name} {user['status']} lancia l'incantesimo: ")
            )

            if _command(url, spell):
                continue
        else:
            seconds_to_wait = randint(1, 3)
            sleep(seconds_to_wait)
            spell = choice(all_spells)

        # send spell
        data = json.dumps({"s": spell}).encode()
        ret = post(
            f"{url}/cast/{user_name}/{enemy_name}",
            data=data,
            headers={"content-type": "application/json"},
        )
        status = ret.json()

        try:
            users = status["game"]["users"]
            user = users[user_name]
            enemy = users[enemy_name]
            f_msg = f"{user_name}: {user['points']}, {enemy_name}: {enemy['points']}\n{{title}}"
            print(f_msg.format(**status))
        except:
            print(status)

if __name__ == '__main__':
    main()