from requests import post, get
import json

from sys import argv

try:
    server = argv[1]
except IndexError:
    server = "localhost:5000"

server = input(f"server [{server}]: ") or server
user_name = input("come ti chiami [harry]? ") or "harry"
print(post(f"http://{server}/user/{user_name}").json())

has_enemy = None
while not has_enemy:
    enemy_name = input("Chi è il tuo avversario [draco]? ") or "draco"
    has_enemy = get(f"http://{server}/user/{enemy_name}").json()
    if not has_enemy:
        print("Il nemico non si è ancora unito al gioco")
    else:
        print(has_enemy)

post(f"http://{server}/start").json()

while True:
    spell = input("incantesimo: ")
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
