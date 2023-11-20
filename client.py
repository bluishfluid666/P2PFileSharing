import threading
import socket
import os

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
port = 55555
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

def publish_file(local_filename, remote_filename):
    with open(local_filename, 'rb') as file:
        file_data = file.read()

    message = f'PUBLISH {remote_filename}\n{file_data}'
    client.sendall(message.encode('utf-8'))

def fetch_file(remote_filename):
    message = f'FETCH {remote_filename}'
    client.sendall(message.encode('utf-8'))

    # Receive file data from server
    file_data = b''
    while True:
        chunk = client.recv(1024)
        if not chunk:
            break
        file_data += chunk

    # Write file data to local file
    with open(remote_filename, 'wb') as file:
        file.write(file_data)

# Sending Message to Server
def write():
    while True:
        message = f'{nickname}: {input("")}'
        command = message.split(":")[1]
        if command.startswith(' publish'):
            local_filename= command.split(' ')[2]
            remote_filename= command.split(' ')[3]
            publish_file(local_filename, remote_filename)
        elif command.startswith(' fetch'):
            remote_filename = command.split(' ', 2)[1]
            fetch_file(remote_filename)
        else:
            print(f'Invalid command: {command}')


receiver_thread = threading.Thread(target=receive)
receiver_thread.start()

sender_thread = threading.Thread(target=write)
sender_thread.start()