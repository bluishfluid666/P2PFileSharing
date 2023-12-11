import socket
import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sv_ttk
import time

FORMAT = "utf-8"
FILE_SEGMENT = 102400

class Utils:
    @staticmethod
    def validate_ip(ip):
        # Regular expression to validate an IP address
        ip_pattern = re.compile("^(\d{1,3}\.){3}\d{1,3}$")
        if ip_pattern.match(ip):
            parts = ip.split(".")
            return all(0 <= int(part) <= 255 for part in parts)
        return False

class Client:
    DEFAULT_SERVER_PORT = 55555
    DEFAULT_LOCAL_PORT = 54321

    def __init__(self):
        self.server_host = ""
        self.server_port = self.DEFAULT_SERVER_PORT
        
        self.local_host = self.get_local_ip()
        self.local_port = self.DEFAULT_LOCAL_PORT
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_file_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.message = " "
        
        self.client_upload_path = ""
        self.client_download_path = ""

        self.list_files = {}

        self.log = []
        
    def get_local_ip(self):
        """
        Get the local IP address of the client.

        Returns:
            str: Local IP address or an error message.
        """
        try:
            # Create a socket object and connect to an external server
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))  # Google's public DNS server and port 80
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except socket.error as e:
            return f"Unable to determine local IP: {str(e)}"
    """
        Setter
    """
    def set_server_host(self, host):
        self.server_host = host
    def set_client_upload_path(self, path):
        self.client_upload_path = path
    def set_client_download_path(self, path):
        self.client_download_path = path
    def set_message(self, message):
        self.message = message    

    """
        Getter
    """
    def get_server_host(self):
        return (self.server_host, self.server_port)
    def get_upload_dir(self):
        return (self.client_upload_path)
    def get_download_dir(self):
        return (self.client_download_path)
    def get_client_host(self):
        return (self.local_host)
    def get_message(self):
        return (self.message)
    
    def print_client(self):
        print(f"Client: {self.local_host}: {self.local_port}")
        print(f"Server: {self.server_host}: {self.server_port}")

    def open_file_serving_socket(self):
        """
            Open a file serving TCP socket, which always runs to listen for file requests.
        """
        self.peer_file_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            """
                The try_except is for testing on the same device (same IP).
                Client 1 will use port 54321. Client 2 has to use port another port - e.g. 64999.
                The file server's port has to be a constant one, i.e. 65000.
            """
            self.peer_file_server.bind((self.get_client_host(), self.DEFAULT_LOCAL_PORT))
        except:
            print("Something went wrong")

        self.peer_file_server.listen()
        print(f"The file serving socket is {self.peer_file_server.getsockname()}")
        while True:
            """
            Accepting connection from client.
            """
            peer_client, peer_client_socket = self.peer_file_server.accept()

            print(f'Prepare to serve {peer_client_socket}...')
            file_name = peer_client.recv(FILE_SEGMENT).decode(FORMAT)
            path = f"{self.get_upload_dir()}/{file_name}"
            print(path)
            file_size = os.path.getsize(path)

            peer_client.send(str(file_size).encode(FORMAT))
            print(f"SENDING: {file_name}\nSIZE: {file_size}")
            with open(path, "rb") as f:
                c = 0
                while c < file_size:
                    # Do stuff with byte.
                    text = f.read(FILE_SEGMENT)
                    # Running loop while c != file_size.
                    if not (text):
                        break
                    peer_client.send(text)
                    c += len(text) 
            status_file = peer_client.recv(FILE_SEGMENT).decode(FORMAT)

            if status_file == "OK":
                print("NICE")
            else :
                print("FAIL")
            
            time.sleep(2)

    def handle_server(self):
    # CONNECT TO SERVER

        self.client_socket.connect(self.get_server_host())

        while True:
            data = self.client_socket.recv(FILE_SEGMENT).decode(FORMAT)
            cmd, msg = data.split('--!--')

            if cmd == 'OK':
                self.log.append(f'{msg}')
            if cmd == 'BEGIN':
                self.client_socket.send(self.get_client_host().encode(FORMAT))
            elif cmd == 'DISCONNECT':
                self.log.append(f'{msg}')
                break
            elif cmd == 'FETCH':
                print(msg)
                new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_ip = msg.split(":")[0]
                client_port = msg.split(":")[1]
                fname = msg.split(":")[2] 
                file = msg.split(":")[3]  

                new_socket.connect((client_ip, int(client_port)))
                new_socket.send(fname.encode(FORMAT)) 
                file_size = new_socket.recv(FILE_SEGMENT).decode(FORMAT)
                print(file_size)
                with open(f"{self.get_download_dir()}/" + file, 'wb') as f: 
                    c = 0
                    while c < int(file_size):
                        print(f"Data: {c}")
                        byte_data = new_socket.recv(FILE_SEGMENT)
                        if not (byte_data):
                            break
                        f.write(byte_data)
                        c += len(byte_data)
                print("DONE")
                new_socket.send("OK".encode(FORMAT))
                f.close()
                new_socket.close()        

            time.sleep(0.1)
            data = self.get_message()
            if (data == " "):
                data = "Waiting"
            cmd_list = data.split(" ")
            cmd = cmd_list[0]

            if cmd == 'Publish' and len(cmd_list) == 3:
                path = f"client_file/{cmd_list[1]}"
                try: 
                    print(path)
                    if (len(cmd_list[2].split(".")) == 1):
                        file_extent = cmd_list[1].split(".")[1]
                        data += f".{file_extent}"
                    self.client_socket.send(data.encode(FORMAT))
                    self.set_message(" ")
                except: 
                    print("Error")
                    data = "Wrong command"
                    self.client_socket.send(data.encode(FORMAT))
            elif cmd == "Waiting":
                self.client_socket.send(cmd.encode(FORMAT))
                self.set_message(" ")

            elif cmd == 'Fetch' and len(cmd_list) == 2:
                self.client_socket.send(data.encode(FORMAT))
                self.set_message(" ")

            elif cmd == 'Disconnect':
                self.client_socket.send(data.encode(FORMAT))
                self.set_message(" ")

            else :
                cmd = "Wrong command"
                self.client_socket.send(data.encode(FORMAT))
                self.set_message(" ")
                
        self.log.append("Disconnecting from server")
        self.client_socket.close()

    def get_files(self):
        receive_list_file = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        receive_list_file.connect((self.server_host, 55556))

        while True:
            while True:
                file_name = receive_list_file.recv(24576).decode('utf-8')
                if (file_name == "DONE"):
                    break
                client_name = receive_list_file.recv(24576).decode('utf-8')
                client_name = client_name.split("|")
                self.list_files[file_name] = client_name

                print(self.list_files)
            time.sleep(5)
            receive_list_file.send("OK@DONE".encode("utf-8"))

    def get_file(self):
        return self.list_files

    def start(self):
        t = threading.Thread(target=self.handle_server, args=())
        t.start()

        get_list = threading.Thread(target=self.get_files, args=())
        get_list.start()

        file_server_thread = threading.Thread(target=self.open_file_serving_socket, args=())
        file_server_thread.start()

class MainApplication(tk.Tk):
    def __init__(self) -> None:
        tk.Tk.__init__(self)

        s = ttk.Style()
        s.theme_use("clam")
        self.client_pack = []

        self.title("Simple file-sharing application")
        self.geometry("600x460")

        self.setup_view = SetupView(self)
        self.setup_view.pack()

class SetupView(ttk.Frame):
    def __init__(self, parent: MainApplication) -> None:

        super().__init__(parent)
        self.parent = parent
        self.create_widgets()
        

    def create_widgets(self) -> None:
        # ### Nickname Entry ###
        # ttk.Label(self, text="Nickname").grid(row=0, column=0)
        # self.nickname_entry = ttk.Entry(self)
        # self.nickname_entry.grid(row=0, column=1, padx=6, pady=4)
        # # Prefill nickname entry with local IP address
        # self.nickname_entry.insert(0, self.client.get_local_ip())
        # self.nickname_entry.configure(state="readonly")
        ttk.Label(self, text="Enter the Client Information", font=("Helvetica", 18, "bold")).grid(row=0, columnspan=3, pady=10)

        # ### Server IP Address Entry ###
        ttk.Label(self, text="Server IP Address").grid(row=2, column=0)
        self.server_ip_entry = ttk.Entry(self, width=30)
        self.server_ip_entry.grid(row=2, column=1, padx=6, pady=4)

        # Working Directory Picker
        ttk.Label(self, text="Upload Directory").grid(row=3, column=0)
        self.upload_dir_entry = ttk.Entry(self, width=30)
        # self.upload_dir_entry.insert(0, os.getcwd() + "/data")
        self.upload_dir_entry.grid(row=3, column=1, padx=6, pady=4)

        self.browse_upload_btn = ttk.Button(self, text="Browse", command=self.upload_folder)
        self.browse_upload_btn.grid(row=3, column=2, padx=6, pady=8)

        # Working Directory Picker
        ttk.Label(self, text="Download Directory").grid(row=4, column=0)
        self.download_dir_entry = ttk.Entry(self, width=30)
        # self.download_dir_entry.insert(0, os.getcwd() + "/data")
        self.download_dir_entry.grid(row=4, column=1, padx=6, pady=4)

        self.browse_download_btn = ttk.Button(self, text="Browse", command=self.download_folder)
        self.browse_download_btn.grid(row=4, column=2, padx=6, pady=8)

        self.continue_button = ttk.Button(
            self, text="Continue", command=self.finish_setup, style="Accent.TButton"
        )
        self.continue_button.grid(row=5, column=0, columnspan=3)

    def upload_folder(self) -> None:
        directory = filedialog.askdirectory(
            initialdir=self.upload_dir_entry.get(), title="Select a folder"
        )
        if directory:
            self.upload_dir_entry.delete(0, tk.END)
            self.upload_dir_entry.insert(0, directory)
            print(f"Upload directory: {directory}")

    def download_folder(self) -> None:
        directory = filedialog.askdirectory(
            initialdir=self.download_dir_entry.get(), title="Select a folder"
        )
        if directory:
            self.download_dir_entry.delete(0, tk.END)
            self.download_dir_entry.insert(0, directory)
            print(f"Download directory: {directory}")

    def finish_setup(self):
        server_host = self.server_ip_entry.get().strip()
        upload_dir = self.upload_dir_entry.get().strip()
        download_dir = self.download_dir_entry.get().strip()

        if not server_host or not upload_dir or not download_dir:
            messagebox.showerror("Invalid Input", "All fields are required.")
            return

        if not Utils.validate_ip(server_host):
            messagebox.showerror("Invalid IP", "The entered IP address is invalid.")
            return

        try:
            self.parent.client_pack.append(server_host)
            self.parent.client_pack.append(upload_dir)
            self.parent.client_pack.append(download_dir)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self.destroy()
        main_view = MainView(self.parent)
        main_view.pack()



class MainView(ttk.Frame):
    def __init__(self, parent: MainApplication) -> None:
        print("Initializing MainView")

        super().__init__(parent)
        self.parent = parent
        self.client = Client()
        self.client.set_server_host(self.parent.client_pack[0])
        self.client.set_client_upload_path(self.parent.client_pack[1])
        self.client.set_client_download_path(self.parent.client_pack[2])

        app = threading.Thread(target=self.create_widgets, args=())
        app.start()

        client_starting = threading.Thread(target=self.client.start, args=())
        client_starting.start()

    def create_widgets(self) -> None:
        print("Creating widgets for MainView")
        self.tab_control = ttk.Notebook(self)

        self.config_tab = HomeTab(self)
        self.tab_control.add(self.config_tab, text="Home")

        self.config_tab = ConfigTab(self)
        self.tab_control.add(self.config_tab, text="Config")

        self.tab_control.pack(expand=1, fill="both")

class HomeTab(ttk.Frame):
    def __init__(self, parent: MainView) -> None:
        print("Initializing MainViewFilesTab")

        super().__init__(parent)
        self.parent = parent
        self.create_widgets()
        self.file = []
        
        self.target_file = ""

    def create_widgets(self) -> None:
        print("Creating widgets for MainViewFilesTab")

        self.files_tree = ttk.Treeview(self)

        # Define tree columns
        self.files_tree["columns"] = (
            "file_name",
            "client",
        )

        # Format columns
        self.files_tree.column("#0", width=0, stretch=tk.NO)
        self.files_tree.column("file_name", anchor=tk.W, width=300)
        self.files_tree.column("client", anchor=tk.W, width=200)

        # Create headings
        self.files_tree.heading("#0", text="", anchor=tk.W)
        self.files_tree.heading("file_name", text="File name", anchor=tk.W)
        self.files_tree.heading("client", text="Client", anchor=tk.W)

        self.files_tree.pack(expand=1, fill="both")

        # Add upload and download buttons
        self.upload_button = ttk.Button(
            self, text="Upload", command=self.upload_file
        )
        self.upload_button.pack(side="left")

        self.download_button = ttk.Button(
            self, text="Download", command=self.download_file
        )
        self.download_button.pack(side="right")

        self.refresh_button = ttk.Button(
            self, text="Refresh", command=self.ping
        )
        self.refresh_button.pack()

        self.disconnect_button = ttk.Button(
            self, text="Disconnect", command=self.disconnect
        )
        self.disconnect_button.pack()
    
    def disconnect(self):
        msg = "Disconnect"
        self.parent.client.set_message(msg)
        print("Disconnected from server")
    def upload_file(self):
        # Implement logic to upload selected file from treeview
        # ... (show file selection dialog, call client upload method) ...
        # Get path of the file to be uploaded
        file_path = filedialog.askopenfilename(title="Select file to upload")

        # Check if user selected a file
        if file_path:
            # Upload the file
            file_dir = self.parent.client.get_upload_dir()

            file_name = file_path.split("/")

            path = ""

            for i in range(len(file_name) - 1):
                path += f"{file_name[i]}/"

            path = path[:-1]
            file_name = file_name[-1]

            if (path != file_dir):
                messagebox.showerror("Error", "You must select a file from Upload Directory")
                print("Wrong file path")
            else:
                file_info_window = FileInfoWindow(self, file_path)
                file_info_window.mainloop()
                print("Correct file path")

            # Update treeview
            self.populate_tree()
        else:
            # Show message if no file is selected
            print("No file selected.")
        print("Press Upload button to upload selected file")

    def download_file(self):
        # Implement logic to download selected file from treeview
        # ... (get selected file name, call client download method) ...
        print(f"File name: {self.target_file}")
        msg = f"Fetch {self.target_file}"
        self.parent.client.set_message(msg)
        print("Press Download button to download selected file")

    def ping(self):
        print("Refreshing file list in MainViewFilesTab")
        self.populate_tree()

    def populate_tree(self) -> None:
        print("Populating file tree in MainViewFilesTab")
        # Clear existing items in the tree
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        self.file = self.parent.client.get_file()
        print(self.file)

        for file in self.file.keys():
            for client in self.file[file]:
                client_file = f"{file} {client}"
                self.files_tree.insert('', tk.END, values=client_file)
                # Bind click events
                self.files_tree.bind("<ButtonRelease-1>", self.on_item_click, add=True)
    
    def on_item_click(self, event):
        # Get selected item
        selected_item = self.files_tree.selection()[0]

        # Extract file information
        file_name, client = self.files_tree.item(selected_item, "values")

        self.target_file = file_name

class FileInfoWindow(tk.Toplevel):
    def __init__(self, parent: HomeTab, file_path):
        super().__init__(parent)
        self.parent = parent
        self.title("File Information")

        # Get file information
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path)

        # Create labels and entry fields
        self.name_label = ttk.Label(self, text="Original Name:")
        self.original_name_entry = ttk.Entry(
            self, width=30, textvariable=tk.StringVar(value=self.file_path)
        )

        self.original_name_entry.insert(0, self.file_path)
        self.original_name_entry.configure(state="readonly")

        self.new_name_label = ttk.Label(self, text="New Name:")
        self.new_name_entry = ttk.Entry(self, width=30)

        self.size_label = ttk.Label(self, text="File Size:")
        self.size_entry = ttk.Entry(self, width=20)
        self.size_entry.insert(0, self.file_size)
        self.size_entry.configure(state="readonly")


        # Layout
        row = 0
        ttk.Label(self, text="").grid(row=row, columnspan=2)  # spacer
        row += 1
        self.name_label.grid(row=row, column=0, sticky="w")
        self.original_name_entry.grid(row=row, column=1, sticky="w")
        row += 1
        self.new_name_label.grid(row=row, column=0, sticky="w")
        self.new_name_entry.grid(row=row, column=1, sticky="w")
        row += 1
        self.size_label.grid(row=row, column=0, sticky="w")
        self.size_entry.grid(row=row, column=1, sticky="w")

        # Save button
        self.save_button = ttk.Button(self, text="Save", command=self.save_filename)
        self.save_button.grid(row=row + 1, column=1, pady=10)

    def save_filename(self):
        original_filename = self.original_name_entry.get().strip()
        new_filename = self.new_name_entry.get().strip()
        file_path, file_ext = os.path.splitext(original_filename)
        file_path = file_path.split("/")[-1]
        
        # Validate the new filename (optional)
        if not new_filename:
            new_filename = file_path

        file_path += file_ext
        new_filename += file_ext

        msg = f"Publish {file_path} {new_filename}"
        
        self.parent.parent.client.set_message(msg)
        print(self.parent.parent.client.get_message())
        self.destroy()

class ConfigTab(ttk.Frame):
    def __init__(self, parent: MainApplication) -> None:
        super().__init__(parent)
        self.parent = parent
        self.create_widgets()

    def create_widgets(self) -> None:
        self.connection_details_frame = MainViewConfigTabConnectionDetails(self)
        self.connection_details_frame.pack(fill="x", padx=10, pady=10)

class MainViewConfigTabConnectionDetails(ttk.Frame):
    def __init__(self, parent: ConfigTab) -> None:
        print("Initializing MainViewSettingsTabConnectionDetails")

        super().__init__(parent)
        self.parent = parent
        self.create_widgets()

    def create_widgets(self) -> None:
        print("Creating widgets for MainViewSettingsTabConnectionDetails")

        ttk.Label(self, text="SERVER INFORMATION", font=("Helvetica", 18, "bold")).grid(row=0, columnspan=2, pady=10)

        ### SERVER IP Entry ###
        ttk.Label(self, text="Client IP address").grid(row=2, column=0)
        self.local_ip_entry = ttk.Entry(self, width=30)
        self.local_ip_entry.grid(row=2, column=1, padx=4, pady=6)
        self.local_ip_entry.insert(0, self.parent.parent.client.get_local_ip())
        self.local_ip_entry.configure(state="readonly")

        ttk.Label(self, text="Upload Directory").grid(row=3, column=0)
        self.local_ip_entry = ttk.Entry(self, width=30)
        self.local_ip_entry.grid(row=3, column=1, padx=4, pady=6)
        self.local_ip_entry.insert(0, self.parent.parent.client.get_upload_dir())
        self.local_ip_entry.configure(state="readonly")

        ttk.Label(self, text="Download Directory").grid(row=4, column=0)
        self.local_ip_entry = ttk.Entry(self, width=30)
        self.local_ip_entry.grid(row=4, column=1, padx=4, pady=6)
        self.local_ip_entry.insert(0, self.parent.parent.client.get_download_dir())
        self.local_ip_entry.configure(state="readonly")

        ttk.Label(self, text="Server Detail").grid(row=5, column=0)
        self.local_ip_entry = ttk.Entry(self, width=30)
        self.local_ip_entry.grid(row=5, column=1, padx=4, pady=6)
        self.local_ip_entry.insert(0, self.parent.parent.client.get_server_host())
        self.local_ip_entry.configure(state="readonly")



if __name__ == "__main__":
    app = MainApplication()

    sv_ttk.use_light_theme()

    app.mainloop()

