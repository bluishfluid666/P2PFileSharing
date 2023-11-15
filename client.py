import threading
import socket

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

ip = input('Enter your server IP: ')
port = 55556
nickname = get_local_ip() + ' ' + str(port)

# Connecting to the Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((ip, port))

# Listening to Server and Sending Nickname
def receive():
    while True:
        try:
            # Receive Message from Server
            # If 'NICK' Send Nickname
            message = client.recv(1024).decode('utf-8')
            if message == 'NICK':
                client.send(nickname.encode('utf-8'))
            else:
                print(message)
        except:
            # Close Connection when Error
            print('An error occured!')
            client.close()
            break

# Sending Message to Server
def write():
    while True:
        message = f'{nickname}: {input("")}'
        
        # TODO: process client's CLI: publish & fetch
        
        client.send(message.encode('utf-8'))


receiver_thread = threading.Thread(target=receive)
receiver_thread.start()

sender_thread = threading.Thread(target=write)
sender_thread.start()

