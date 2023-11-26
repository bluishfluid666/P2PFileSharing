#!/usr/bin/env python3

import os
import re
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sv_ttk
from client import Client, CLI as ClientCLI

port = 55556

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Utils:
    @staticmethod
    def validate_ip(ip):
        # Regular expression to validate an IP address
        ip_pattern = re.compile("^(\d{1,3}\.){3}\d{1,3}$")
        if ip_pattern.match(ip):
            parts = ip.split(".")
            return all(0 <= int(part) <= 255 for part in parts)
        return False


class ApplicationContext:
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing ApplicationContext")
        self.ip = None
        self.port = None
        self.nickname = None
        self.working_dir = None
        self.client = None

    def connect(self, ip: str, port: int, nickname: str, working_dir: str) -> None:
        self.logger.info(
            f"Attempting to connect: IP={ip}, Port={port}, Nickname='{nickname}', WorkingDir='{working_dir}'"
        )
        if self.client is not None:
            self.logger.info("Closing existing client connection.")
            self.client.close()

        self.client = Client(ip, port, nickname)
        self.client.connect()

        self.ip = ip
        self.port = port
        self.nickname = nickname
        self.working_dir = working_dir
        self.logger.info("Connection established.")


class MainApplication(tk.Tk):
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing MainApplication")

        self.ctx = ApplicationContext()

        tk.Tk.__init__(self)

        s = ttk.Style()
        s.theme_use("clam")

        self.title("Simple file-sharing application")
        self.geometry("640x400")

        self.setup_view = SetupView(self, self.ctx)
        self.setup_view.pack()
        self.logger.info("MainApplication UI setup complete")


class SetupView(ttk.Frame):
    def __init__(self, parent: MainApplication, ctx: ApplicationContext) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing SetupView")

        super().__init__(parent)
        self.parent = parent
        self.ctx = ctx
        self.create_widgets()

    def create_widgets(self) -> None:
        self.logger.info("Creating widgets for SetupView")
        ### Nickname Entry ###
        ttk.Label(self, text="Nickname").grid(row=0, column=0)
        self.nickname_entry = ttk.Entry(self)
        self.nickname_entry.grid(row=0, column=1, padx=6, pady=4)
        # Prefill nickname entry with local IP address
        self.nickname_entry.insert(0, ClientCLI.get_local_ip() + " " + str(port))

        ### Server IP Address Entry ###
        ttk.Label(self, text="Server IP Address").grid(row=1, column=0)
        self.server_ip_entry = ttk.Entry(self)
        self.server_ip_entry.grid(row=1, column=1, padx=6, pady=4)

        # Working Directory Picker
        ttk.Label(self, text="Working Directory").grid(row=2, column=0)
        self.working_dir_entry = ttk.Entry(self)
        self.working_dir_entry.insert(0, os.getcwd() + "/data")
        self.working_dir_entry.grid(row=2, column=1, padx=6, pady=4)

        self.browse_button = ttk.Button(self, text="Browse", command=self.browse_folder)
        self.browse_button.grid(row=2, column=2, padx=6, pady=8)

        self.continue_button = ttk.Button(
            self, text="Continue", command=self.finish_setup, style="Accent.TButton"
        )
        self.continue_button.grid(row=3, column=0, columnspan=3)

    def browse_folder(self) -> None:
        self.logger.info("Browsing for folder in SetupView")
        directory = filedialog.askdirectory(
            initialdir=self.working_dir_entry.get(), title="Select a folder"
        )
        if directory:
            self.working_dir_entry.delete(0, tk.END)
            self.working_dir_entry.insert(0, directory)

    def finish_setup(self) -> None:
        nickname = self.nickname_entry.get().strip()
        ip_address = self.server_ip_entry.get().strip()
        working_dir = self.working_dir_entry.get().strip()

        self.logger.info(
            f"Finishing setup with Nickname='{nickname}', IP='{ip_address}', WorkingDir='{working_dir}'"
        )

        if not nickname or not ip_address or not working_dir:
            messagebox.showerror("Invalid Input", "All fields are required.")
            return

        if not Utils.validate_ip(ip_address):
            messagebox.showerror("Invalid IP", "The entered IP address is invalid.")
            return

        try:
            self.ctx.connect(ip_address, port, nickname, working_dir)
            self.logger.info("Setup finished and connection attempted in SetupView")
        except Exception as e:
            self.logger.error(f"Error during setup finish in SetupView: {e}")
            messagebox.showerror("Error", str(e))
            return

        self.destroy()
        main_view = MainView(self.parent, self.ctx)
        main_view.pack()


class MainView(ttk.Frame):
    def __init__(self, parent: MainApplication, ctx: ApplicationContext) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing MainView")

        super().__init__(parent)
        self.parent = parent
        self.ctx = ctx
        self.create_widgets()

    def create_widgets(self) -> None:
        self.logger.info("Creating widgets for MainView")
        self.tab_control = ttk.Notebook(self)

        self.files_tab = MainViewFilesTab(self, self.ctx)
        self.network_tab = MainViewNetworkTab(self, self.ctx)
        self.settings_tab = MainViewSettingsTab(self, self.ctx)

        self.tab_control.add(self.files_tab, text="Files")
        self.tab_control.add(self.network_tab, text="Network")
        self.tab_control.add(self.settings_tab, text="Settings")

        self.tab_control.pack(expand=1, fill="both")


class MainViewFilesTab(ttk.Frame):
    def __init__(self, parent: MainView, ctx: ApplicationContext) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing MainViewFilesTab")

        super().__init__(parent)
        self.parent = parent
        self.ctx = ctx
        self.create_widgets()
        self.files = []

    def create_widgets(self) -> None:
        self.logger.info("Creating widgets for MainViewFilesTab")
        self.files_tree = ttk.Treeview(self)

        # Define tree columns
        self.files_tree["columns"] = (
            "file_name",
            "size",
            "type",
            "last_modified",
            "status",
        )

        # Format columns
        self.files_tree.column("#0", width=0, stretch=tk.NO)
        self.files_tree.column("file_name", anchor=tk.W, width=200)
        self.files_tree.column("size", anchor=tk.W, width=100)
        self.files_tree.column("type", anchor=tk.W, width=100)
        self.files_tree.column("last_modified", anchor=tk.W, width=100)
        self.files_tree.column("status", anchor=tk.W, width=100)

        # Create headings
        self.files_tree.heading("#0", text="", anchor=tk.W)
        self.files_tree.heading("file_name", text="File Name", anchor=tk.W)
        self.files_tree.heading("size", text="Size", anchor=tk.W)
        self.files_tree.heading("type", text="Type", anchor=tk.W)
        self.files_tree.heading("last_modified", text="Last Modified", anchor=tk.W)
        self.files_tree.heading("status", text="Status", anchor=tk.W)

        self.files_tree.pack(expand=1, fill="both")

        self.refresh_button = ttk.Button(
            self, text="Refresh", command=self.refresh_file_list
        )
        self.refresh_button.pack()

        self.upload_button = ttk.Button(self, text="Upload", command=self.upload_file)
        self.upload_button.pack()

    def refresh_file_list(self):
        self.logger.info("Refreshing file list in MainViewFilesTab")
        # Add code to refresh file list
        self.populate_tree()

    def populate_tree(self) -> None:
        self.logger.info("Populating file tree in MainViewFilesTab")
        # Clear existing items in the tree
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        # Insert new file data into the tree
        for i, file_data in enumerate(self.files):
            self.files_tree.insert("", "end", iid=i, values=file_data)

    def upload_file(self):
        self.logger.info("Uploading file in MainViewFilesTab")
        file_path = filedialog.askopenfilename()
        if file_path:
            self.logger.info(f"Selected file for upload: {file_path}")
            self.open_save_file_dialog(file_path)
        else:
            self.logger.info("File upload cancelled.")

    def open_save_file_dialog(self, file_path):
        self.logger.info(f"Opening save file dialog for: {file_path}")
        save_file_dialog = SaveFileDialog(self, file_path)
        save_file_dialog.grab_set()


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


class MainViewNetworkTab(ttk.Frame):
    def __init__(self, parent: MainView, ctx: ApplicationContext) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing MainViewNetworkTab")

        super().__init__(parent)
        self.parent = parent
        self.ctx = ctx
        self.create_widgets()

    def create_widgets(self) -> None:
        self.logger.info("Creating widgets for MainViewNetworkTab")


class MainViewSettingsTab(ttk.Frame):
    def __init__(self, parent: MainView, ctx: ApplicationContext) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing MainViewSettingsTab")

        super().__init__(parent)
        self.parent = parent
        self.ctx = ctx
        self.create_widgets()

    def create_widgets(self) -> None:
        self.logger.info("Creating widgets for MainViewSettingsTab")
        self.connection_details_frame = MainViewSettingsTabConnectionDetails(
            self, self.ctx
        )
        self.connection_details_frame.pack(fill="x", padx=10, pady=10)


class MainViewSettingsTabConnectionDetails(ttk.Frame):
    def __init__(self, parent: MainViewSettingsTab, ctx: ApplicationContext) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing MainViewSettingsTabConnectionDetails")

        super().__init__(parent)
        self.parent = parent
        self.ctx = ctx
        self.create_widgets()

    def create_widgets(self) -> None:
        self.logger.info("Creating widgets for MainViewSettingsTabConnectionDetails")

        ttk.Label(self, text="Nickname").grid(row=0, column=0)
        self.nickname_entry = ttk.Entry(self)
        self.nickname_entry.grid(row=0, column=1, padx=6, pady=4)
        self.nickname_entry.insert(0, self.ctx.nickname)

        ttk.Label(self, text="Server IP Address").grid(row=1, column=0)
        self.server_ip_entry = ttk.Entry(self)
        self.server_ip_entry.grid(row=1, column=1, padx=6, pady=4)
        self.server_ip_entry.insert(0, self.ctx.ip)

        ttk.Label(self, text="Working Directory").grid(row=2, column=0)
        self.working_dir_entry = ttk.Entry(self)
        self.working_dir_entry.grid(row=2, column=1, padx=6, pady=4)
        self.working_dir_entry.insert(0, self.ctx.working_dir)

        self.browse_button = ttk.Button(self, text="Browse", command=self.browse_folder)
        self.browse_button.grid(row=2, column=2)

        self.save_button = ttk.Button(
            self, text="Save", command=self.save, style="Accent.TButton"
        )
        self.save_button.grid(row=3, column=0, columnspan=3, padx=6, pady=8)

    def browse_folder(self) -> None:
        self.logger.info("Browsing for folder in MainViewSettingsTabConnectionDetails")
        directory = filedialog.askdirectory(
            initialdir=self.working_dir_entry.get(), title="Select a folder"
        )
        if directory:
            self.working_dir_entry.delete(0, tk.END)
            self.working_dir_entry.insert(0, directory)

    def save(self) -> None:
        self.logger.info("Saving settings in MainViewSettingsTabConnectionDetails")
        nickname = self.nickname_entry.get().strip()
        ip_address = self.server_ip_entry.get().strip()
        working_dir = self.working_dir_entry.get().strip()

        self.logger.info(
            f"Settings to save: Nickname='{nickname}', IP='{ip_address}', WorkingDir='{working_dir}'"
        )

        if not nickname or not ip_address or not working_dir:
            messagebox.showerror("Invalid Input", "All fields are required.")
            return

        if not Utils.validate_ip(ip_address):
            messagebox.showerror("Invalid IP", "The entered IP address is invalid.")
            return

        try:
            self.ctx.connect(ip_address, port, nickname, working_dir)

        except Exception as e:
            messagebox.showerror("Error", e)
            return

        self.destroy()
        main_view = MainView(self.parent, self.ctx)
        main_view.pack()


if __name__ == "__main__":
    app = MainApplication()

    sv_ttk.use_light_theme()

    app.mainloop()
