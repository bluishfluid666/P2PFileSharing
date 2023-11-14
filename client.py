import threading
import socket

nickname = input('Choose your nickname: ')

# Connecting to the Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('0.0.0.0', 55556))

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
        client.send(message.encode('utf-8'))


receiver_thread = threading.Thread(target=receive)
receiver_thread.start()

sender_thread = threading.Thread(target=write)
sender_thread.start()

