# [CLIENT]
# Imported modules
import os
import socket
import hashlib
import tkinter as tk
from tkinter import messagebox, filedialog, ttk, simpledialog
import time

# Constant Variables
IP = 'localhost'
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = 'utf-8'

class UI:
    # UI Variables
    SIZE_X = 415
    SIZE_Y = 400

    # Name: open_frame
    # Param1: frame - the frame being opened
    # Return: None
    # Desc: Opens a frame as the highest priority
    def open_frame(self, frame):
        frame.tkraise()

    # Name: open_file
    # Param: None
    # Return: file - whatever selected file directory
    # Desc: Grabs a file
    def open_file(self):
        file = filedialog.askopenfilename(title='Select File')
        print(f'Accessed file: {file}')
        return file
    
    # Name: upload_file
    # Param: conn - the connection to the server
    # Return: None
    # Desc: Uploads a file to the server data storage
    def upload_file(self, conn):
        try:
            file_path = self.open_file()

            # If the file path exists
            if file_path:
                # Starts the upload request
                conn.send("UPLOAD".encode(FORMAT))
                file_name = os.path.basename(file_path)
                conn.send(file_name.encode(FORMAT))
                time.sleep(0.1)
                
                # Handles opening and loading chunk by chunk
                with open(file_path, "rb") as f:
                    while chunk := f.read(SIZE):
                        conn.send(chunk)

                # Sends a final bit message
                conn.send(b"EOF")

                # Handles final confirmations
                response = conn.recv(SIZE).decode(FORMAT)
                print("Server response:", response)

                # Updates the current program status
                self.status_var.set(f"Uploaded {file_name} successfully.")

        except ConnectionAbortedError as e:
            # Handles ConnectionAborted errors
            print(f"Connection Aborted: {e}")
            messagebox.showerror("Connection Error", "Connection was unexpectedly closed.")
        
        except Exception as e:
            # Handles Exception errors
            print(f"An error occurred: {e}")


    # Name: download_file
    # Param: conn - the connection to the server
    # Return: None
    # Desc: Downloads a file from the server data storage to the client computer
    def download_file(self, conn):
        # Prompt for file name to download
        file_name = simpledialog.askstring("Download File", "Enter the file name to download:")
        if not file_name:
            return

        # Send download request to the server
        conn.send("DOWNLOAD".encode(FORMAT))
        conn.send(file_name.encode(FORMAT))  # Send the requested file name
        time.sleep(0.1)  # Allow server time to process

        # Prepare to save the downloaded file locally
        save_path = filedialog.asksaveasfilename(title="Save File As", initialfile=file_name)
        if not save_path:
            print("Download cancelled.")
            return

        # Start receiving file data
        with open(save_path, "wb") as f:
            print(f"Downloading {file_name}...")
            while True:
                chunk = conn.recv(SIZE)
                print("Received Chunk")
                
                if chunk == b"EOF":  # End of file signal
                    print("File download completed.")
                    self.status_var.set(f"{file_name} downloaded successfully!")
                    break
                elif chunk.startswith(b"ERROR@"):
                    # Decode error messages only, since they are text-based
                    error_msg = chunk.decode(FORMAT)
                    print("Server error:", error_msg)
                    messagebox.showerror("Download Error", error_msg.split("@")[1])
                    return
                else:
                    # Write binary data to the file without decoding
                    print("Writes chunk")
                    f.write(chunk)

        print(f"Downloaded file saved to: {save_path}")


    # Name: delete_file
    # Param: conn - the connection to the server
    # Return: None
    # Desc: Deletes a file from the server data storage
    def delete_file(self, conn):
        conn.send('DELETE'.encode(FORMAT))
        self.status_var.set('Deleting file...')

    # Name: authenticate
    # Param1: conn - The connection
    # Param2: username - The entered username
    # Param3: password - The entered password
    # Return: None
    # Desc: Handles uploading the username and password from the client
    def authenticate(self, conn, username, password):
        while True:
            data = conn.recv(SIZE).decode(FORMAT)
            if 'Username:' in data:
                conn.send(username.encode(FORMAT))
            elif 'Password:' in data:
                password_hashed = hashlib.sha256(password.encode()).hexdigest()
                print(f'Client: Sending hashed password: {password_hashed}')
                conn.send(password_hashed.encode(FORMAT))
            elif 'OK' in data:
                print(f'{data}')
                messagebox.showinfo('Permission Verified', f'{data}\nValid user/password')
                self.open_frame(self.fd_frame)
                return
            elif 'ERROR' in data:
                print(f'{data}')
                messagebox.showerror('Permission Denied', f'{data}\nInvalid user/password')
                conn.send('OK@LOGOUT'.encode(FORMAT))
                self.root.destroy()
                return

    # Name: setup_fd_frame
    # Param: conn - The connection to the server
    # Return: None
    # Desc: Sets up the File Directory and Transfer frame
    def setup_fd_frame(self, conn):
        self.fd_frame = tk.Frame(self.root, height=self.SIZE_Y, width=self.SIZE_X, padx=20, pady=20, bg="lightgrey")
        self.fd_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # First Label - Title for the file transfer system
        self.fd_lb1 = tk.Label(self.fd_frame, text='File Transfer System', font=('Helvetica', 16, 'bold'), bg="lightgrey")
        self.fd_lb1.grid(row=0, column=0, padx=10, pady=10)

        # Status Label
        self.status_var = tk.StringVar()
        self.status_var.set("Status: Ready")
        self.status_label = tk.Label(self.fd_frame, textvariable=self.status_var, fg="blue", bg="lightgrey", font=('Helvetica', 10, 'italic'))
        self.status_label.grid(row=1, column=0, padx=10, pady=10)

        # File Operation Buttons
        self.button_frame = tk.Frame(self.fd_frame, bg="lightgrey")
        self.button_frame.grid(row=2, column=0, pady=10)

        self.upload_btn = tk.Button(self.button_frame, text='Upload File', width=15,
                                    command=lambda: self.upload_file(conn=conn), bg="#007BFF", fg="white")
        self.upload_btn.grid(row=0, column=0, padx=5, pady=5)

        self.download_btn = tk.Button(self.button_frame, text='Download File', width=15,
                                      command=lambda: self.download_file(conn=conn), bg="#28A745", fg="white")
        self.download_btn.grid(row=0, column=1, padx=5, pady=5)

        self.delete_btn = tk.Button(self.button_frame, text='Delete File', width=15,
                                    command=lambda: self.delete_file(conn=conn), bg="#DC3545", fg="white")
        self.delete_btn.grid(row=0, column=2, padx=5, pady=5)

    # Name: setup_au_frame
    # Param: conn - The connection to the server
    # Return: None
    # Desc: Sets up the Authentication frame
    def setup_au_frame(self, conn):
        self.au_frame = tk.Frame(self.root, height=self.SIZE_Y, width=self.SIZE_X, padx=20, pady=20, bg="lightgrey")
        self.au_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title for the Authentication process
        self.au_lb1 = tk.Label(self.au_frame, text='Authentication Process', font=('Helvetica', 16, 'bold'), bg="lightgrey")
        self.au_lb1.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        # Username Entry
        self.au_lb2 = tk.Label(self.au_frame, text='Username:', bg="lightgrey", font=('Helvetica', 12))
        self.au_lb2.grid(row=1, column=0, sticky=tk.E, padx=5)
        self.au_box1 = tk.Entry(self.au_frame, font=('Helvetica', 12))
        self.au_box1.grid(row=1, column=1, padx=5, pady=5)

        # Password Entry
        self.au_lb3 = tk.Label(self.au_frame, text='Password:', bg="lightgrey", font=('Helvetica', 12))
        self.au_lb3.grid(row=2, column=0, sticky=tk.E, padx=5)
        self.au_box2 = tk.Entry(self.au_frame, show='*', font=('Helvetica', 12))
        self.au_box2.grid(row=2, column=1, padx=5, pady=5)

        # Make Connection Button
        self.au_b1 = tk.Button(self.au_frame, text='Make Connection', font=('Helvetica', 12), width=15,
                               command=lambda: self.authenticate(conn=conn, username=self.au_box1.get(), password=self.au_box2.get()),
                               bg="#17A2B8", fg="white")
        self.au_b1.grid(row=3, column=0, columnspan=2, padx=10, pady=15)

    # Name: __init__
    # Param: None
    # Return: None
    # Desc: Sets up the UI for the application upon the creation of a new UI class
    def __init__(self):
        # Sets up connection
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(ADDR)
            print("Connected to server.")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to the server: {e}")
            return

        # Setting up root
        self.root = tk.Tk()
        self.root.title("File Transfer Application")


        # Calculating position
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int((screen_width - self.SIZE_X) / 2)
        center_y = int((screen_height - self.SIZE_Y) / 2)
        self.root.geometry(f'{self.SIZE_X}x{self.SIZE_Y}+{center_x}+{center_y}')
        self.root.resizable(False, False)

        # Sets up frames
        self.setup_fd_frame(client)
        self.setup_au_frame(client)

        # Opens starting frame
        self.open_frame(self.au_frame)

        # Runs the UI
        self.root.mainloop()

        # Confirm disconnection
        print('Disconnected from the server.')
        client.close()

# Name: main
# Param: None
# Return: None
# Desc: Handles connecting to a server (We're the Client)
def main():
    ui = UI()

# runs main
if __name__ == '__main__':
    main()
