#!/usr/bin/env python3

import threading
import socket


class Client:
    def __init__(self, ip: str, port: int, nickname: str) -> None:
        self.ip = ip
        self.port = port
        self.nickname = nickname
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self) -> None:
        self.socket.connect((self.ip, self.port))

    def recv(self, buffer_size: int) -> bytes:
        return self.socket.recv(buffer_size)

    def send(self, text: str) -> int:
        return self.socket.send(text.encode("utf-8"))

    def close(self) -> None:
        self.socket.close()

    def publish_file(local_filename, remote_filename):
        with open(local_filename, "rb") as file:
            file_data = file.read()

        message = f"PUBLISH {remote_filename}\n{file_data}"
        self.socket.sendall(message.encode("utf-8"))

    def fetch_file(remote_filename):
        message = f"FETCH {remote_filename}"
        self.socket.sendall(message.encode("utf-8"))

        """
            For example, if the index server returns a list of peer file servers,
            the peer client chooses the one with IP address 192.168.1.15
        """
        selected_ip_address = "192.168.1.15"
        peer_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_client.connect((selected_ip_address, 65000))
        # TODO: implement fetch


class CLI:
    def __init__(self) -> None:
        self.ip: str = input("Enter your server IP: ")
        self.port: int = 55556
        self.nickname: str = CLI.get_local_ip() + " " + str(self.port)
        self.client: Client = Client(self.ip, self.port, self.nickname)
        self.receiver_thread: threading.Thread = threading.Thread(target=self.receive)
        self.sender_thread: threading.Thread = threading.Thread(target=self.write)
        self.running: bool = True

    @staticmethod
    def get_local_ip() -> str:
        try:
            # Create a socket object and connect to an external server
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except socket.error:
            return "Unable to determine local IP"

    def receive(self) -> None:
        while self.running:
            try:
                message: str = self.client.recv(1024).decode("utf-8")
                if message == "NICK":
                    self.client.send(self.nickname)
                else:
                    print(message)
            except socket.error as e:
                print(e)
                print("An error occurred!")
                self.stop()

    def write(self) -> None:
        while self.running:
            message = f'{nickname}: {input("")}'
            print(message)
            command = message.split(":")[-1]
            if command.startswith(" publish"):
                local_filename = command.split(" ")[2]
                remote_filename = command.split(" ")[3]
                publish_file(local_filename, remote_filename)
            elif command.startswith(" fetch"):
                remote_filename = command.split(" ", 2)[1]
                fetch_file(remote_filename)
            else:
                print(f"Invalid command: {command}")

    def start(self) -> None:
        print(
            f"Starting client with nickname: {self.nickname} on {self.ip}:{self.port}"
        )

        self.client.connect()
        print("Connected to server!")

        self.receiver_thread.start()
        self.sender_thread.start()

    def stop(self) -> None:
        self.running = False
        self.client.close()


if __name__ == "__main__":
    cli: CLI = CLI()

    cli.start()
