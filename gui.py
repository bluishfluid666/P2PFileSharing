#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog
from client import Client, CLI as ClientCLI

port = 55556


class MainApplication(tk.Tk):
    def __init__(self) -> None:
        tk.Tk.__init__(self)
        self.title("Simple file-sharing application")
        self.geometry("400x400")
        self.ip_entry_view = IPEntryView(self)
        self.ip_entry_view.pack()

    def connect(self, ip: str, port: int) -> None:
        self.client = Client(ip, port, "Client")
        self.client.connect()


class IPEntryView(tk.Frame):
    def __init__(self, main: MainApplication) -> None:
        super().__init__(main)
        self.main = main
        self.create_widgets()

    def create_widgets(self) -> None:
        self.nickname_label = tk.Label(self, text="Enter your nickname:")
        self.nickname_label.pack()

        self.nickname_entry = tk.Entry(self)
        self.nickname_entry.pack()

        # prefill nickname entry with local IP address
        self.nickname_entry.insert(0, ClientCLI.get_local_ip() + " " + str(port))

        self.ip_label = tk.Label(self, text="Enter Server IP Address:")
        self.ip_label.pack()

        self.ip_entry = tk.Entry(self)
        self.ip_entry.pack()

        self.submit_button = tk.Button(self, text="Submit", command=self.submit_ip)
        self.submit_button.pack()

    def submit_ip(self) -> None:
        ip_address: str = self.ip_entry.get()
        print("IP Address entered:", ip_address)

        try:
            self.main.connect(ip_address, port)
        except ConnectionRefusedError:
            return

        self.destroy()  # Destroy current view
        file_transfer_view = FileTransferView(self.main)
        file_transfer_view.pack()


class FileTransferView(tk.Frame):
    def __init__(self, main: MainApplication) -> None:
        super().__init__(main)
        self.create_widgets()

    def create_widgets(self) -> None:
        # Column 1: File selection
        self.file_selection_frame = tk.Frame(self)
        self.file_selection_frame.grid(row=0, column=0, padx=10, pady=10)

        self.select_file_button = tk.Button(
            self.file_selection_frame, text="Select File", command=self.select_file
        )
        self.select_file_button.pack()

        # Column 2: File listing and download
        self.file_listing_frame = tk.Frame(self)
        self.file_listing_frame.grid(row=0, column=1, padx=10, pady=10)

        self.file_list_label = tk.Label(
            self.file_listing_frame, text="Available Files:"
        )
        self.file_list_label.pack()

        self.file_listbox = tk.Listbox(self.file_listing_frame)
        self.file_listbox.pack()

        self.download_button = tk.Button(
            self.file_listing_frame,
            text="Download Selected File",
            command=self.download_file,
        )
        self.download_button.pack()

    def select_file(self) -> None:
        file_path: str = filedialog.askopenfilename()
        print("Selected file:", file_path)
        # Implement file upload functionality

    def download_file(self) -> None:
        # Implement file download functionality
        pass


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
