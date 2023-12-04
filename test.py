message = "192.168.146.132 55555: ubuntu"
name = message.split(":")[-1].split(" ")[-1]
ip = message.split(":")[0]
port = ip.split(" ")[1]
ip = ip.split(" ")[0]
print(ip, port)