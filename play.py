import json
import urllib.parse

import kazoo.client

zk = kazoo.client.KazooClient()
zk.start()
zk.delete("/Animals", recursive=True)
zk.delete("/Fruits", recursive=True)
zk.delete("/Vegetables", recursive=True)
zk.ensure_path("/Animals/Elephant")
zk.ensure_path("/Animals/Dolphin")
zk.ensure_path("/Animals/Monkey")
zk.ensure_path("/Animals/Monkey/BetaMonkey")
zk.ensure_path("/Animals/Monkey/GammaMonkey")
zk.ensure_path("/Animals/Monkey/AlphaMonkey")
zk.ensure_path("/Fruits/Watermelon")
zk.ensure_path("/Fruits/Banana")
zk.ensure_path("/Fruits/Orange")
zk.ensure_path("/Fruits/Apple")
zk.ensure_path("/Vegetables/Broccoli")
zk.ensure_path("/Vegetables/Tomato")
zk.ensure_path("/Vegetables/Potato")
zk.ensure_path("/Vegetables/Union")
zk.ensure_path("/Vegetables/Cucumber")
zk.set("/Animals/Dolphin", b"This is a dolphin")
zk.set("/Vegetables/Potato", b"This is a potato")
path = urllib.parse.quote("/Animals/Dragon?hello=world&lorem=ipsum&foo=bar")
zk.ensure_path(path)
zk.set(path, json.dumps(dict(hello="world", lorem="ipsum", foo="bar")).encode())

print(zk.get_children("/Fruits"))
print(zk.get("/Fruits"))
