import socket
import threading

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
    
# CONSTANTS
SERVER_IP = input("Enter server IP: ")
PORT = 55555
FILE_SERVING_PORT = 54321
SERVER_ADDR = (SERVER_IP, PORT)
FORMAT = "utf-8"
NAME = input("Enter your name: ")
nickname = get_local_ip() + " " + str(PORT)  

def open_file_serving_socket():
    """
        Open a file serving TCP socket, which always runs to listen for file requests.
    """
    peer_file_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_file_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        """
            The try_except is for testing on the same device (same IP).
            Client 1 will use port 54321. Client 2 has to use port another port - e.g. 64999.
            The file server's port has to be a constant one, i.e. 65000.
        """
        peer_file_server.bind((get_local_ip(), FILE_SERVING_PORT))
    except:
        print("Something went wrong")

    peer_file_server.listen()
    print(f"The file serving socket is {peer_file_server.getsockname()}")
    while True:
        """
        Accepting connection from client.
        """
        peer_client, peer_client_socket = peer_file_server.accept()
        print(f'Prepare to serve {peer_client_socket}...')
        file_name = peer_client.recv(1024).decode(FORMAT)
        path = f"client_file/{file_name}"
        with open(path) as f:
            text = f.read(1024)
            while text:
                peer_client.send(text.encode(FORMAT))
                text = f.read(1024)
        break

def handle_server():
    # CONNECT TO SERVER
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(SERVER_ADDR)

    while True:
        data = client_socket.recv(1024).decode(FORMAT)
        cmd, msg = data.split('--!--')

        if cmd == 'OK':
            print(f'{msg}')
        elif cmd == 'DISCONNECT':
            print(f'{msg}')
            break
        elif cmd == 'FETCH':
            print(f'{msg}')
            new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_ip = msg.split(":")[0]
            client_port = msg.split(":")[1]
            fname = msg.split(":")[2] 
            file = msg.split(":")[3]  
            new_socket.connect((client_ip, int(client_port)))
            new_socket.send(fname.encode(FORMAT)) 
            f = open("downloads/" + file, "wb")
            while True:
                msg_data = new_socket.recv(1024)
                if msg_data:
                    f.write(msg_data)
                if not msg_data:
                    break
            f.close()
            new_socket.close()        

        print("> ", end="")
        data = input()
        cmd_list = data.split(" ")
        cmd = cmd_list[0]

        if cmd == 'Publish' and len(cmd_list) == 3:
            path = f"client_file/{cmd_list[1]}"
            try: 
                with open(path) as f:
                    text = f.read()
                if (len(cmd_list[2].split(".")) == 1):
                    file_extent = cmd_list[1].split(".")[1]
                    data += f".{file_extent}"
                client_socket.send(data.encode(FORMAT))
            except: 
                print("Error")
                data = "Wrong command"
                client_socket.send(data.encode(FORMAT))

        elif cmd == 'Fetch' and len(cmd_list) == 2:
            client_socket.send(data.encode(FORMAT))

        elif cmd == 'Disconnect':
            client_socket.send(data.encode(FORMAT))

        else :
            cmd = "Wrong command"
            client_socket.send(data.encode(FORMAT))
            
    print("Disconnecting from server")
    client_socket.close()

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((get_local_ip(), 54321))
    s.listen(5)

    try:
        t = threading.Thread(target=handle_server, args=())
        t.start()

        file_server_thread = threading.Thread(target=open_file_serving_socket)
        file_server_thread.start()
            
    except:
        print("Shutting down")

if __name__ == "__main__":
    main()