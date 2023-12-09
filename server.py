import socket
import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sv_ttk
import time

class Server:
    def __init__(self):
        self.host = self.get_local_ip()
        self.port = 55555

        self.file_port = 55556

        self.log = []
        
        # Print IP address to terminal
        self.log.append(f'Host is on: {self.host}')
        self.log.append("SERVER IS STARTING")
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.settimeout(1)
        self.server_socket.listen()

        self.send_file_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_file_socket.bind((self.host, self.file_port))
        self.send_file_socket.settimeout(1)
        self.send_file_socket.listen()

        self.log.append("SERVER IS LISTENING")

        self.client_addr = []
        self.active_addr = []
        self.client_lname = {}
        self.client_file = {}

    def send_list(self):
        try:
            conn, addr = self.send_file_socket.accept()
            while True:
                for file in self.client_file.keys():
                    conn.send(file.encode('utf-8'))
                    time.sleep(0.5)
                    client_name = ""

                    for client in self.client_file[file]:
                        client_name += f"{client}|"
                    client_name = client_name[:-1]
                    conn.send(client_name.encode('utf-8'))
                    time.sleep(0.5)

                conn.send("DONE".encode('utf-8'))

                data = conn.recv(204800).decode("utf-8")
                data = data.split("@")
                cmd = data[0]

                if cmd == "OK":
                    time.sleep(3)
                    pass
                else:
                    self.log.append("Error sending list file")
        except: 
            pass

    def get_local_ip(self):
        try:
            # Create a socket object and connect to an external server
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))  # Google's public DNS server and port 80
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except socket.error:
            return "Unable to determine local IP"
        
    def get_log(self):
        return self.log
    
    def get_server_ip(self):
        return self.host
    
    def get_client(self):
        return self.active_addr
    
    def get_file(self, addr):
        addr_file_list = []
        for file in self.client_file.keys():
            if addr in self.client_file[file]:
                addr_file_list.append(file)
        
        return addr_file_list
    
    def handle_client(self, conn, addr):
        self.log.append(f'[NEW CONNECTION] {addr} connected')
        conn.send("BEGIN--!--Welcome To The Server".encode("utf-8"))
        aut_addr = conn.recv(204800).decode("utf-8")

        self.active_addr.append(aut_addr)
        new_conn = aut_addr in self.client_addr

        if (new_conn != True):
            self.client_addr.append(aut_addr)

        while True: 
            data = conn.recv(204800).decode("utf-8")
            data = data.split(" ")
            cmd = data[0]

            if cmd == 'Publish':
                lname = data[1]
                fname = data[2]
            
                send_data = "OK--!--Publish Successfully"
                if fname in self.client_file:
                    if aut_addr in self.client_file[fname]: 
                        send_data = "OK--!--File is already published"
                    else :
                        self.client_file[fname].append(aut_addr)
                        self.client_lname[fname] = lname
                else :
                    self.client_file[fname] = []
                    self.client_file[fname].append(aut_addr)
                    self.client_lname[fname] = lname

                self.log.append(f"{aut_addr}: USING PUBLISH")
                self.log.append(self.client_file)          
                conn.send(send_data.encode("utf-8"))
            
            elif cmd == 'Fetch':
                self.log.append(self.client_lname)
                file = data[1]
                if (file in self.client_file):
                    peer_ip = self.client_file.get(file)[0]
                    send_data = "FETCH--!--"
                    send_data += f"{peer_ip}:54321"
                    send_data += f":{self.client_lname[file]}"
                    send_data += f":{file}"

                self.log.append(f"{aut_addr}: USING FETCH")
                conn.send(send_data.encode("utf-8")) 

            elif cmd == 'Disconnect':
                send_data = "DISCONNECT--!--Goodbye"
                conn.send(send_data.encode("utf-8"))
                break
            elif cmd == "Waiting":
                send_data = "OK--!--Waiting..."
                conn.send(send_data.encode("utf-8"))
            else :
                send_data = f"OK--!--Wrong command from {aut_addr}"
                conn.send(send_data.encode('utf-8'))
        
        self.active_addr.remove(aut_addr)
        self.log.append(f"[DISCONNECTED] {aut_addr} disconnected")
    
    def starting_server(self):
        while True: 
            try:
                conn, addr = self.server_socket.accept()
                client_command = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_command.start()

                sending_list = threading.Thread(target=self.send_list, args=())
                sending_list.start()
            except :
                pass
    

class MainApplication(tk.Tk):
    def __init__(self) -> None:
        tk.Tk.__init__(self)
        print("Initializing MainViewSettingsTab")

        s = ttk.Style()
        s.theme_use("clam")

        self.title("Simple file-sharing application")
        self.geometry("600x460")

        self.main_view = MainView(self)
        self.main_view.pack()

class MainView(ttk.Frame):
    def __init__(self, parent: MainApplication) -> None:
        print("Initializing MainView")

        super().__init__(parent)
        self.parent = parent
        self.server = Server()
        
        app = threading.Thread(target=self.create_widgets, args=())
        app.start()

        server_starting = threading.Thread(target=self.server.starting_server, args=())
        server_starting.start()

    def create_widgets(self) -> None:
        print("Creating widgets for MainView")
        self.tab_control = ttk.Notebook(self)

        self.home_tab = HomeTab(self)
        self.tab_control.add(self.home_tab, text="Home")

        self.log_tab = LogTab(self)
        self.tab_control.add(self.log_tab, text="Logs")

        self.config_tab = ConfigTab(self)
        self.tab_control.add(self.config_tab, text="Config")

        self.tab_control.pack(expand=1, fill="both")

class HomeTab(ttk.Frame):
    def __init__(self, parent: MainView) -> None:
        print("Initializing MainViewFilesTab")

        super().__init__(parent)
        self.parent = parent
        self.create_widgets()
        self.clients = []

    def create_widgets(self) -> None:
        print("Creating widgets for MainViewFilesTab")

        self.files_tree = ttk.Treeview(self)

        # Define tree columns
        self.files_tree["columns"] = (
            "Client",
            "last_modified",
            "status",
        )

        # Format columns
        self.files_tree.column("#0", width=0, stretch=tk.NO)
        self.files_tree.column("Client", anchor=tk.W, width=200)
        self.files_tree.column("last_modified", anchor=tk.W, width=100)
        self.files_tree.column("status", anchor=tk.W, width=100)

        # Create headings
        self.files_tree.heading("#0", text="", anchor=tk.W)
        self.files_tree.heading("Client", text="Client", anchor=tk.W)
        self.files_tree.heading("last_modified", text="Last Join", anchor=tk.W)
        self.files_tree.heading("status", text="Status", anchor=tk.W)

        self.files_tree.pack(expand=1, fill="both")

        # Add Label and Button

        # Create frame for IP address and button
        self.ip_address_frame = ttk.Frame(self)

        # Add Label and Entry for IP address
        self.ip_address_label = ttk.Label(self.ip_address_frame, text="Enter IP address:")
        self.ip_address_entry = ttk.Entry(self.ip_address_frame)

        self.ip_address_label.pack(side=tk.LEFT, padx=5)
        self.ip_address_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Add Discover button
        self.discover_button = ttk.Button(self.ip_address_frame, text="Discover", command=self.discover)
        self.discover_button.pack(side=tk.RIGHT)

        # Pack the frame
        self.ip_address_frame.pack(fill=tk.X)

        self.refresh_button = ttk.Button(
            self, text="Refresh", command=self.ping
        )
        self.refresh_button.pack()

    def ping(self):
        print("Refreshing file list in MainViewFilesTab")
        # Add code to refresh file list
        self.populate_tree()

    def populate_tree(self) -> None:
        print("Populating file tree in MainViewFilesTab")
        # Clear existing items in the tree
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        self.clients = self.parent.server.get_client()

        # Insert new file data into the tree
        for i, client_ip in enumerate(self.clients):
           client = f"{client_ip} - Active"
           self.files_tree.insert('', tk.END, iid=i, values=client)

    def discover(self):
        #TODO: Show the file of the addr 
        client_ip = self.ip_address_entry.get().strip()

        # Validate the IP address
        if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", client_ip):
            messagebox.showerror("Error", "Invalid IP address")
            return

        # Get file list from the server
        files = self.parent.server.get_file(client_ip)

        # If no files found
        if not files:
            messagebox.showinfo("Info", f"No files found on client {client_ip}")
            return

        # Create a new window to display files
        files_window = FileListWindow(self, client_ip, files)
        files_window.grab_set()

class FileListWindow(tk.Toplevel):
    def __init__(self, parent, client_ip, files):
        super().__init__(parent)
        self.parent = parent
        self.client_ip = client_ip
        self.files = files

        self.title(f"Files on {client_ip}")
        self.geometry("500x300")

        # Create a frame to hold the list
        self.files_frame = ttk.Frame(self)
        self.files_frame.pack(expand=True, fill="both")

        # Create a listbox to show files
        self.files_list = tk.Listbox(self.files_frame)
        for file in files:
            self.files_list.insert(tk.END, file)
        self.files_list.pack(expand=True, fill="both")

        self.close_button = ttk.Button(self, text="Close", command=self.destroy)
        self.close_button.pack(side=tk.RIGHT)

class SaveFileDialog(tk.Toplevel):
    def __init__(self, parent, file_path):
        super().__init__(parent)
        self.parent = parent
        self.file_path = file_path
        self.create_widgets()

    def create_widgets(self):
        self.file_path_label = ttk.Label(self, text="File Path:")
        self.file_path_label.grid(row=0, column=0)

        self.file_path_entry = ttk.Entry(self)
        self.file_path_entry.grid(row=0, column=1, padx=6, pady=4)

        self.browse_button = ttk.Button(
            self, text="Browse", command=self.browse_file_path
        )
        self.browse_button.grid(row=0, column=2)

        self.save_button = ttk.Button(
            self, text="Save", command=self.save_file, style="Accent.TButton"
        )
        self.save_button.grid(row=1, column=0, columnspan=3, padx=6, pady=8)

    def browse_file_path(self):
        file_path = filedialog.asksaveasfilename()
        if file_path:
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, file_path)

    def save_file(self):
        save_path = self.file_path_entry.get().strip()
        if save_path:
            # Save the file to the specified path
            # self.ctx.client.publish_file(self.file_path, save_path)
            messagebox.showinfo("Success", "File saved successfully!")
            self.destroy()
        else:
            messagebox.showerror(
                "Error", "Please enter a valid file path.", parent=self
            )

class LogTab(ttk.Frame):
    def __init__(self, parent: MainApplication) -> None:
        super().__init__(parent)
        self.parent = parent
        self.log_text = tk.Text(self)
        self.create_widgets()

    def create_widgets(self) -> None:
        self.log_text.pack(expand=True, fill="both")

        # Add button to fetch logs
        self.refresh_button = ttk.Button(
            self, text="Refresh", command=self.fetch_logs
        )
        self.refresh_button.pack()

    def fetch_logs(self):
        # Get logs from server
        logs = self.parent.server.get_log()

        # Clear existing log text
        self.log_text.delete("1.0", tk.END)

        # Insert new log entries
        for entry in logs:
            self.log_text.insert(tk.END, f"{entry}\n")

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
        ttk.Label(self, text="Server IP address").grid(row=2, column=0)
        self.server_ip_entry = ttk.Entry(self)
        self.server_ip_entry.grid(row=2, column=1, padx=4, pady=6)
        self.server_ip_entry.insert(0, self.parent.parent.server.get_server_ip())
        self.server_ip_entry.configure(state="readonly")

if __name__ == "__main__":
    
    app = MainApplication()

    sv_ttk.use_light_theme()

    app.mainloop()