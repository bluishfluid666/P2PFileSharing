import random
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


index_server_ip = input('Enter your server IP: ')
port = 55556
name = input('Enter your name: ')
local_ip = get_local_ip()

# Connecting to the index server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((index_server_ip, port))
print(f"The client socket is {client.getsockname()}")
client_ip, client_port = client.getsockname()
nickname = f"{client_ip}:{client_port}:name"

FILE_SERVING_PORT = 65000


def open_file_serving_socket():
    """
        Open a file serving TCP socket, which always runs to listen for file requests.
    """
    peer_file_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_file_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        """
            The try_except is for testing on the same device (same IP).
            Client 1 will use port 65000. Client 2 has to use port another port - e.g. 64999.
            The file server's port has to be a constant one, i.e. 65000.
        """
        peer_file_server.bind((local_ip, FILE_SERVING_PORT))
    except:
        peer_file_server.bind((local_ip, 64999))
    peer_file_server.listen()
    print(f"The file serving socket is {peer_file_server.getsockname()}")
    while True:
        """
        Accepting connection from client.
        """
        peer_client, peer_client_socket = peer_file_server.accept()
        print(f'Prepare to serve {peer_client_socket}...')
        peer_client.send('Good evening!'.encode('utf-8'))


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

    """
        For example, if the index server returns a list of peer file servers,
        the peer client chooses the one with IP address 192.168.1.15
    """
    selected_ip_address = '192.168.1.15'
    peer_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_client.connect((selected_ip_address, 65000))
    # TODO: implement fetch


# Sending Message to Server
def write():
    while True:
        message = f'{nickname}: {input("")}'
        print(message)
        command = message.split(":")[-1]
        if command.startswith(' publish'):
            local_filename = command.split(' ')[2]
            remote_filename = command.split(' ')[3]
            publish_file(local_filename, remote_filename)
        elif command.startswith(' fetch'):
            remote_filename = command.split(' ', 2)[1]
            fetch_file(remote_filename)
        else:
            print(f'Invalid command: {command}')


file_server_thread = threading.Thread(target=open_file_serving_socket)
file_server_thread.start()

receiver_thread = threading.Thread(target=receive)
receiver_thread.start()

sender_thread = threading.Thread(target=write)
sender_thread.start()
