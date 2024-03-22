import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import paramiko
import threading
import os
import requests
import tempfile
import shutil
import zipfile

CURRENT_VERSION = "1.0"  # Replace with your current version

# Import sv_ttk module
try:
    import sv_ttk
except ImportError:
    # Handle the case where sv_ttk is not available
    pass

class SSHCredentialsDialog(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Username:").grid(row=0, sticky="e")
        tk.Label(master, text="Password:").grid(row=1, sticky="e")

        self.username_entry = ttk.Entry(master)
        self.password_entry = ttk.Entry(master, show='*')

        self.username_entry.grid(row=0, column=1)
        self.password_entry.grid(row=1, column=1)

        return self.username_entry  # initial focus

    def apply(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.result = (username, password)


class PiVPNManager:
    def __init__(self, root):
        self.root = root
        self.root.title("PiVPN Manager v1.0 by hozaCo")
        self.root.geometry("1500x500")  # Adjusted window size

        # Apply the "dark" theme using sv_ttk
        try:
            sv_ttk.set_theme("dark")
        except NameError:
            # Handle the case where sv_ttk is not available
            pass

        # Create main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Left Frame for SSH Connection Progress
        self.ssh_frame = ttk.Frame(self.main_frame)
        self.ssh_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # SSH Treeview
        self.ssh_columns = ["Progress"]
        self.ssh_tree = ttk.Treeview(self.ssh_frame, columns=self.ssh_columns, show="headings", selectmode="browse")
        for col in self.ssh_columns:
            self.ssh_tree.heading(col, text=col)
        self.ssh_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right Frame for Client Management
        self.client_frame = ttk.Frame(self.main_frame)
        self.client_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # IP Address Entry
        tk.Label(self.client_frame, text="PiVPN IP Address:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.ip_entry = ttk.Entry(self.client_frame, width=20)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Connect Button
        ttk.Button(self.client_frame, text="Connect", command=self.connect).grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Client Management Frame
        client_management_frame = ttk.Frame(self.client_frame)
        client_management_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky="nsew")

        # Label for Client Management Group
        tk.Label(client_management_frame, text="Client Management").grid(row=0, column=0, columnspan=4, pady=5)

        # Client Management Buttons
        ttk.Button(client_management_frame, text="Create Connection", command=self.create_connection).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(client_management_frame, text="Remove Client", command=self.remove_client).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(client_management_frame, text="List Clients", command=self.list_clients).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(client_management_frame, text="List Connected Clients", command=self.list_connected_clients).grid(row=1, column=3, padx=5, pady=5)
        ttk.Button(client_management_frame, text="Update", command=self.update_application).grid(row=1, column=4, padx=5, pady=5)

        # Output Frame
        self.output_frame = ttk.Frame(self.client_frame)
        self.output_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        # Output Treeview
        columns = ["Name", "Remote IP", "Virtual IP", "Bytes Received", "Bytes Sent", "Last Seen"]
        self.output_tree = ttk.Treeview(self.output_frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.output_tree.heading(col, text=col)
        self.output_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for Output Treeview
        scrollbar = ttk.Scrollbar(self.output_frame, orient="vertical", command=self.output_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_tree.configure(yscrollcommand=scrollbar.set)

        # SSH Connection
        self.ssh_client = None

        # Add Exit Button
        ttk.Button(self.client_frame, text="Exit", command=self.root.quit).grid(row=3, column=0, columnspan=3, pady=10)

    def list_clients(self):
        if not self.ssh_client:
            self.update_output("Not connected. Please connect first.")
            return

        # Start a new thread for listing clients
        threading.Thread(target=self.list_clients_thread).start()

    def list_clients_thread(self):
        command = "pivpn -l"
        output = self.execute_ssh_command(command)
        self.update_output(output)

    def connect(self):
        ip_address = self.ip_entry.get()
        if ip_address:
            self.ssh_tree.delete(*self.ssh_tree.get_children())
            self.ssh_tree.insert("", tk.END, values=("Connecting..."))

            # Create a custom dialog for both username and password
            dialog = SSHCredentialsDialog(self.root, title="SSH Credentials")
            if dialog.result:
                username, password = dialog.result
                
                # Start a new thread for the SSH connection
                threading.Thread(target=self.perform_ssh_connection, args=(ip_address, username, password)).start()

    def perform_ssh_connection(self, ip_address, username, password):
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(ip_address, username=username, password=password, timeout=10)
            self.ssh_tree.delete(*self.ssh_tree.get_children())
            self.ssh_tree.insert("", tk.END, values=("Connected"))
        except Exception as e:
            self.ssh_tree.delete(*self.ssh_tree.get_children())
            self.ssh_tree.insert("", tk.END, values=(f"Connection Error: {e}"))

    def create_connection(self):
        if not self.ssh_client:
            self.update_output("Not connected. Please connect first.")
            return

        client_name = self.get_client_name()

        if client_name:
            command = f"pivpn -a -n {client_name}"
            threading.Thread(target=self.execute_create_connection_command, args=(command,)).start()

    def execute_create_connection_command(self, command):
        output = self.execute_ssh_command(command)
        self.update_output(output)

    def remove_client(self):
        if not self.ssh_client:
            self.update_output("Not connected. Please connect first.")
            return

        # Start a new thread for listing clients for removal
        threading.Thread(target=self.list_clients_thread_for_removal).start()

    def list_clients_thread_for_removal(self):
        command = "pivpn -l"
        output = self.execute_ssh_command(command)

        # Process the output to get the list of clients
        client_list = [line.strip() for line in output.split('\n') if line.strip()]

        if not client_list:
            self.update_output("No clients to remove.")
            return

        # Initialize client_index to None
        client_index = None

        try:
            # Display a dialog to choose the client number
            client_choices = "\n".join([f"{i + 1}) {client}" for i, client in enumerate(client_list[1:])])
            client_index = simpledialog.askinteger("Choose a Client", f"Client list:\n{client_choices}\nPlease enter the Index of the Client to be removed:", minvalue=1, maxvalue=len(client_list)-1)
        except tk.TclError:
            # Handle the case where the dialog window is closed or deleted
            self.update_output("Operation canceled by the user.")
            return

        if client_index is not None:
            # Remove the selected client
            command = f"pivpn -r {client_list[client_index]}"
            removal_output = self.execute_ssh_command(command)
            self.update_output(removal_output)


    def list_connected_clients(self):
        if not self.ssh_client:
            self.update_output("Not connected. Please connect first.")
            return

        # Start a new thread for listing connected clients
        threading.Thread(target=self.list_connected_clients_thread).start()

    def list_connected_clients_thread(self):
        command = "pivpn -c"
        output = self.execute_ssh_command(command)
        # Remove header from output
        output_lines = output.split("\n")[1:]
        cleaned_output = "\n".join(output_lines)
        self.update_output(cleaned_output)

    def execute_ssh_command(self, command):
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            return stdout.read().decode('utf-8').strip()
        except Exception as e:
            return f"Error executing command: {e}"

    def update_output(self, text):
        self.output_tree.delete(*self.output_tree.get_children())  # Clear previous entries
        lines = text.split('\n')
        for line in lines:
            values = line.split()
            self.output_tree.insert("", tk.END, values=values)

    def get_client_name(self):
        client_name = simpledialog.askstring("Client Name", "Enter client name:")
        return client_name

    def update_application(self):
        try:
            latest_version = self.get_latest_version()
            if latest_version > CURRENT_VERSION:
                response = messagebox.askyesno("Update Available", f"New version {latest_version} available. Do you want to update?")
                if response:
                    self.download_and_install_update()
            else:
                messagebox.showinfo("No Updates", "You are already using the latest version.")
        except Exception as e:
            messagebox.showerror("Error", f"Error updating application: {e}")

    def get_latest_version(self):
        response = requests.get("https://api.github.com/repos/<username>/<repository>/releases/latest")
        if response.status_code == 200:
            data = response.json()
            return data['tag_name']
        else:
            raise Exception("Failed to retrieve latest version information.")

    def download_and_install_update(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            download_url = "https://github.com/<username>/<repository>/releases/latest/download/<filename>.zip"
            download_path = os.path.join(temp_dir, "update.zip")
            with requests.get(download_url, stream=True) as r:
                with open(download_path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)

            # Extract the downloaded zip file
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Replace the current application files with the updated files
            update_dir = os.path.join(temp_dir, "<directory_name>")
            for root, dirs, files in os.walk(update_dir):
                for file in files:
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), file)
                    shutil.copy(src_file, dest_file)

            messagebox.showinfo("Update Complete", "Update successful. Please restart the application.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PiVPNManager(root)
    root.mainloop()
