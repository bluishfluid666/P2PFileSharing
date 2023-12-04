from config_server import *
import threading

client_addr = []
active_addr = []
client_lname = []
client_file = {}

def server_command():
    while True:
        cmd = input()
        if cmd == "Discover":
            print(client_file)
        elif cmd == "Disconnect":
            break;
        else :
            print("Wrong command")
    return True

def handle_client(conn, addr):
    print(f'[NEW CONNECTION] {addr} connected')
    conn.send("OK--!--Welcome To The Server".encode(FORMAT))
    active_addr.append(addr[0])
    new_conn = addr[0] in client_addr

    if (new_conn != True):
        client_addr.append(addr[0])

    while True: 
        data = conn.recv(BUFFER_SIZE).decode(FORMAT)
        data = data.split(" ")
        cmd = data[0]

        if cmd == 'Publish':
            lname = data[1]
            fname = data[2]
        
            send_data = "OK--!--Publish Successfully"
            if fname in client_file:
                if addr[0] in client_file[fname]: 
                    send_data = "OK--!--File is already published"
                else :
                    client_file[fname].append(addr[0])
            else :
                client_file[fname] = []
                client_file[fname].append(addr[0])
                client_lname.append(lname)

            print(f"{addr}: USING PUBLISH")
            print(client_file)          
            conn.send(send_data.encode(FORMAT))
        
        elif cmd == 'Fetch':
            file = data[1]
            if (file in client_file):
                peer_ip = client_file.get(file)[0]
                send_data = "FETCH--!--"
                send_data += f"{peer_ip}:54321"
                send_data += f":{client_lname[0]}"
                send_data += f":{file}"

            print(f"{addr}: USING FETCH")
            conn.send(send_data.encode(FORMAT)) 

        elif cmd == 'Disconnect':
            send_data = "DISCONNECT--!--Goodbye"
            conn.send(send_data.encode(FORMAT))
            break
        else :
            send_data = f"OK--!--Wrong command from {addr}"
            conn.send(send_data.encode('utf-8'))
    
    active_addr.remove(addr[0])
    print(f"[DISCONNECTED] {addr} disconnected")
def main():
    # Print IP address to terminal
    print(f'Host is on: {HOST_IP}')
    print("SERVER IS STARTING")
    # Initialize server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(SERVER_ADDR)
    server_socket.settimeout(1)
    server_socket.listen()
    print("SERVER IS LISTENING")

    while True: 
        try:
            conn, addr = server_socket.accept()
            client_command = threading.Thread(target=handle_client, args=(conn, addr))
            client_command.start()

            handle_server = threading.Thread(target=server_command)
            handle_server.start()
        except :
            pass

if __name__ == "__main__":
    main()