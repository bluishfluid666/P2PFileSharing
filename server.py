import threading
import socket
from pynput import keyboard

# This is used to get the IP of the host
def get_local_ip():
    try:
        # Create a socket object and connect to an external server
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))  # Google's public DNS server and port 80
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except socket.error:
        return "Unable to determine local IP"

BUFFER_SIZE = 1024
host = get_local_ip()
print(f'Host is on: {host}')
port = 55556

# Initializing server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((host, port))
server.settimeout(1)
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
    while listener.is_alive():
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
    while listener.is_alive():
        # Accepting Connection
        try:
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
            threadList.append(thread)
        except:
            #Timeout, do again until press esc
            pass

# This is used to listen for server commands: discover & ping
def server_console():
    while listener.is_alive():
        command = input()

# This is used to track if the server is pressed ESC to stop or not
def on_release(key):
    if key == keyboard.Key.esc:
        # Stop listener
        return False

threadList = []

# Collect events until released
with keyboard.Listener(on_release=on_release)as listener:
    thread = threading.Thread(target=receive)
    thread.start()
    threadList.append(thread)
    
    thread = threading.Thread(target=server_console)
    thread.start()
    threadList.append(thread)

    for thread in threadList:
        thread.join()
        threadList.remove(thread)
    
    listener.join()