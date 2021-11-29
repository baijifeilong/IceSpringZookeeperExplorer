import kazoo.client

zk = kazoo.client.KazooClient()
print(zk, zk.connected)
zk.start()
print(zk, zk.connected)
print("root", zk.get("/"))
print("children", zk.get_children("/"))
