from requests import post, get
import json

from sys import argv
from requests import get
from pathlib import Path
from threading import Thread


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
    except ImportError:
        pass


def main(server):
    print("\n\n\nPòno Pòtter\n\n\n")
    server = input(f"server [{server}]: ") or server
    user_name = input("come ti chiami [harry]? ") or "harry"
    user = post(f"http://{server}/user/{user_name}").json()
    print(user)

    has_enemy = None
    while not has_enemy:
        enemy_name = input("Chi è il tuo avversario [draco]? ") or "draco"
        has_enemy = get(f"http://{server}/user/{enemy_name}").json()
        if not has_enemy:
            print("Il nemico non si è ancora unito al gioco")
        else:
            print(has_enemy)

    post(f"http://{server}/restart").json()
    while True:
        spell = input(iconize(f"{user_name} {user['status']} lancia l'incantesimo: "))
        data = json.dumps({"s": spell}).encode()
        ret = post(
            f"http://{server}/cast/{user_name}/{enemy_name}",
            data=data,
            headers={"content-type": "application/json"},
        )
        status = ret.json()

        try:
            users = status["game"]["users"]
            user = users[user_name]
            enemy = users[enemy_name]
            f_msg = f"{user_name}: {{game[users][{user_name}][points]}}, {enemy_name}: {{game[users][{enemy_name}][points]}}\n{{title}}"
            print(f_msg.format(**status))
        except:
            print(status)


if __name__ == "__main__":
    try:
        server = argv[1]
    except IndexError:
        server = "localhost:5000"
    t = Thread(target=play_music)
    t.start()
    main(server)
    t.join()
