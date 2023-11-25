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

    # `publish <lname> <fname>` a local file a local file (which is stored in the client’s
    # file system as lname) is added to the client’s repository as a file named fname,
    # which is then conveyed to the server.
    def publish(self, lname: str, fname: str) -> None:
        self.send(f"publish {lname} {fname}")

    # `fetch <fname>` fetch some copy of the target file and add it to the local repository
    def fetch(self, fname: str) -> None:
        self.send(f"fetch {fname}")
        # TODO


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
            message: str = f'{self.nickname}: {input("")}'
            self.client.send(message)

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
