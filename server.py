import threading
import socket

host = socket.gethostbyname('warmachine.local')
port = 55556

# Initializing server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((host, port))
server.listen()

# Lists for Clients and their Nicknames

clients = []
nicknames = []

# Sending message to all connected clients

def broadcast(message):
    for client in clients:
        client.send(message)

# Handling messages from clients
def handle(client):
    while True:
        try:
            # Broadcasting Messages
            message = client.recv(1024)
            broadcast(message)
        except:
            # Removing and Closing Clients
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            broadcast(f'{nickname} has left the chat!')
            nicknames.remove(nickname)
            break

# Receiving/ Listening function
def receive():
    while True:
        # Accepting Connection
        client, address = server.accept()
        print(f'Connected with {address}')

        # Request And Store Client Information
        client.send('NICK'.encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        nicknames.append(nickname)
        clients.append(client)

        # Print and Broadcast Nickname
        print(f'Nickname is {nickname}')
        broadcast(f'{nickname} joined!'.encode('utf-8'))

        # Start Handling Thread for Client
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

receive()