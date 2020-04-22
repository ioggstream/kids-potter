from requests import post
import json

default_server = "localhost:5000"
server = input(f"server [{default_server}]: ") or default_server
user_name = input("come ti chiami [harry]? ") or "harry"
print(post(f"http://{server}/user/{user_name}").json())
enemy_name = input("Chi è il tuo avversario [draco]? ") or "draco"
print(post(f"http://{server}/user/{enemy_name}").json())

while True:
  spell = input("incantesimo: ")
  data = json.dumps({"s": spell}).encode()
  ret = post(
    f"http://{server}/cast/{user_name}/{enemy_name}",
    data=data,
    headers={
    "content-type": "application/json"
  })
  status = ret.json()

  try:
    users = status['game']['users']
    user = users[user_name]
    enemy = users[enemy_name]
    f_msg = f"{user_name}: {{game[users][{user_name}][points]}}, {enemy_name}: {{game[users][{enemy_name}][points]}}\n{{title}}"
    print(f_msg.format(**status))
  except:
    print(status)
