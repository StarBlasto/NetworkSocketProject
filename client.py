# [CLIENT]
# Imported modules
import os
import socket
import hashlib
import tkinter as tk
from tkinter import messagebox, filedialog, ttk, simpledialog
import time
#from tqdm import tqdm

# Constant Variables
IP = '10.200.102.17'
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = 'utf-8'

class UI:
    # UI Variables
    SIZE_X = 540
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
            # Gets file path
            file_path = self.open_file()
            selected_folder = self.file_listbox.get(tk.ACTIVE)

            # Determines if the file is a directory
            target_folder = (
                selected_folder.strip('[Folder] ') if '[Folder]' in selected_folder else ''
            )

            # Check if the file exists
            if file_path:
                # Send request to UPLOAD file
                conn.send('UPLOAD'.encode(FORMAT))
                veri = conn.recv(SIZE).decode(FORMAT)
                file_name = os.path.basename(file_path)

                # Send the target directory path
                conn.send(f'{target_folder}/{file_name}'.encode(FORMAT))

                # Check if the file already exists on the server
                server_resp = conn.recv(SIZE).decode(FORMAT)
                if server_resp == 'ALREADY EXISTS':
                    confirm = messagebox.askyesno(
                        'File Already exists', f'Would you like to overwrite the file?'
                    )
                    conn.send('YES'.encode(FORMAT) if confirm else 'NO'.encode(FORMAT))
                    if not confirm:
                        return
                else:
                    conn.send('N/A'.encode(FORMAT))

                # Get file size
                file_size = os.path.getsize(file_path)

                # Transfer the file in chunks
                with open(file_path, 'rb') as f:
                    chunk_index = 0
                    print('Opened file')
                    while chunk := f.read(SIZE):
                        conn.send(chunk)
                        ack = conn.recv(SIZE).decode(FORMAT)
                        if ack == f'ACK@{chunk_index}':
                            print(f"Server acknowledged chunk {chunk_index}")
                            #self.status_var.set(f'Uploaded Chunk: {chunk_index}')
                            #self.root.update_idletasks()

                            chunk_index += 1  # Move to the next chunk
                        elif "ERROR@" in ack:
                            print(f"Server reported an error for chunk {chunk_index}, resending...")
                        elif ack == "ACK@EOF":
                            print("Server acknowledged EOF, upload complete")
                            break

                print('Sent final EOF chunk')
                conn.send(b'EOF')

                # Handle server response
                response = conn.recv(SIZE).decode(FORMAT)
                print(f'Server response: {response}')

                conn.send('Ack'.encode(FORMAT))

                # Get upload speed
                upload_speed = conn.recv(SIZE).decode(FORMAT)
                print(f'Upload Speed: {upload_speed}')

                # Update status
                self.status_var.set(
                    f'Uploaded {file_name} to {target_folder} successfully\nUpload Speed: {upload_speed} MB/s'
                )
                self.update_file_list(conn)

        except ConnectionAbortedError as e:
            # Handle connection errors
            print(f'Connection Aborted: {e}')
            messagebox.showerror('Connection Error', 'Connection was unexpectedly closed')

        except Exception as e:
            # Handle other exceptions
            print(f'ERROR: {e}')


    # Name: create_subdirectory
    # Param1: conn - The connection
    # Return: None
    # Desc: Creates a subdirectory in the server storage
    def create_subdirectory(self, conn):
        # Gathers directory name
        dir_name = simpledialog.askstring('Create Subdirectory', 'Enter subdirectory name:')
        if dir_name:
            # Sends request to CREATE DIRECTORY
            conn.send('CREATE_DIR'.encode(FORMAT))
            veri = conn.recv(SIZE).decode(FORMAT)

            # Sends Info about Directory
            conn.send(dir_name.encode(FORMAT))
            
            # Waits for confirmation message
            response = conn.recv(SIZE).decode(FORMAT)
            if response == 'DIR_CREATED':
                messagebox.showinfo('Success', f'Subdirectory {dir_name} created')
                self.update_file_list(conn)
            else:
                messagebox.showerror('Error', f'Failed to create subdirectory: {response}')

    # Name: update_file_list
    # Param1: conn - The connection
    # Return: None
    # Desc: Updates the directory of files
    def update_file_list(self, conn):
        # Sends request to open the DIRECTORY
        conn.send('DIR'.encode(FORMAT))
        data = conn.recv(SIZE).decode(FORMAT)

        # Clears current file list
        self.file_listbox.delete(0, tk.END)

        # verifies the list isn't empty
        if data != 'Empty':
            lines = data.split('\n')
            
            # Adds a name for aech line
            for line in lines:
                if line:
                    indent_level = line.count('/')
                    indent = '   ' * indent_level
                    if line.endswith('/'):
                        display = f'[Folder] {line.strip("/")}'
                    else:
                        display = f'{indent}[File] {line}'
                    self.file_listbox.insert(tk.END, display)
       # else:
            # There are no files
            #self.file_listbox.insert(tk.END, 'No files available')

    # Name: download_file
    # Param: conn - the connection to the server
    # Return: None
    # Desc: Downloads a file from the server data storage to the client computer
    def download_file(self, conn):
        # Prompt for file name to download
        file_name = self.file_listbox.get(tk.ACTIVE)
        if not file_name:
            messagebox.showwarning('Download Warning', 'No file selected')
            return
        
        # Removes the Prenames and Indents from the file
        item_path = file_name.replace('[File]', '').replace('[Folder]', '').strip()
        item_path = item_path.replace('   ', '/').strip('- ')

        # Sends request to DOWNLOAD the file
        conn.send('DOWNLOAD'.encode(FORMAT))
        veri = conn.recv(SIZE).decode(FORMAT)

        # Sends info about the FILE
        conn.send(item_path.encode(FORMAT))

        # Handles base_name incase of file path stuff
        base_name = os.path.basename(item_path)

        # Prepare to save the downloaded file locally
        save_path = filedialog.asksaveasfilename(title='Save File As', initialfile=base_name)
        if not save_path:
            print('Download cancelled')
            return
        
        # Opens the file to download
        with open(save_path, 'wb') as opened_file:
            while True:
                print('Waiting for Chunk...')
                chunk = conn.recv(SIZE)

                if b'EOF' in chunk:
                    # The final chunk from the TCP
                    print('Final Chunk (EOF received)')
                    opened_file.write(chunk.split(b'EOF')[0])

                    # Sends confirmation
                    conn.send('CONFIRM'.encode(FORMAT))

                    # Gets download speed
                    download_speed = conn.recv(SIZE).decode(FORMAT)
                    print(f'Upload Speed: {download_speed}')

                    self.status_var.set(f'{file_name} downloaded successfully!\nDownload Speed: {download_speed} MB/s')
                    break
                elif chunk.startswith(b'ERROR@'):
                    # There was an error
                    error_msg = chunk.decode(FORMAT)
                    messagebox.showerror('Download Error', error_msg.split('@')[1])
                    return
                
                # Average chunk sending
                print(f'Writing Chunk: {chunk[:5]}')
                opened_file.write(chunk)
        
        # Verifies file has been sent
        print(f'Downloaded file saved to: {save_path}')

    # Name: delete_file
    # Param: conn - the connection to the server
    # Return: None
    # Desc: Deletes a file or directory from the server data storage
    def delete_file(self, conn):
        # Get selected item from the listbox
        selected_item = self.file_listbox.get(tk.ACTIVE)
        if not selected_item:
            messagebox.showwarning('Delete Warning', 'No item selected')
            return
        
        # Confirms if you want to delete this file from the server
        confirm = messagebox.askyesno('Delete Confirmation', f'Are you sure you want to delete {selected_item}?')
        if not confirm:
            return

        # Removes prename and indentation
        item_path = selected_item.replace('[File]', '').replace('[Folder]', '').strip()
        item_path = item_path.replace('   ', '/').strip('- ')

        # Send delete request to the server with the cleaned path
        conn.send('DELETE'.encode(FORMAT))
        veri = conn.recv(SIZE).decode(FORMAT)

        # Info about what file to delete
        conn.send(item_path.encode(FORMAT))

        # Receive response from the server
        response = conn.recv(SIZE).decode(FORMAT)
        if response == 'FILE_DELETED':
            # Verifies file has been deleted
            messagebox.showinfo('Delete Success', f'{item_path} deleted successfully')
            self.status_var.set(f'{item_path} deleted successfully')
        elif response.startswith('ERROR@'):
            # There was an error
            error_msg = response.split('@')[1]
            messagebox.showerror('Delete Error', error_msg)
            self.status_var.set(f'Error: {error_msg}')

        # Refresh the file list
        self.update_file_list(conn=conn)

    # Name: authenticate
    # Param1: conn - The connection
    # Param2: username - The entered username
    # Param3: password - The entered password
    # Return: None
    # Desc: Handles uploading the username and password from the client
    def authenticate(self, conn, username, password):
        while True:
            # Gets the data from the server
            data = conn.recv(SIZE).decode(FORMAT)

            if 'Username:' in data:
                # Requesting username
                conn.send(username.encode(FORMAT))

            elif 'Password:' in data:
                # Requestinig password
                password_hashed = hashlib.sha256(password.encode()).hexdigest()
                print(f'Client: Sending hashed password: {password_hashed}')
                conn.send(password_hashed.encode(FORMAT))

            elif 'OK' in data:
                # An OK message was verified
                print(f'{data}')
                messagebox.showinfo('Permission Verified', f'{data}\nValid user/password')
                self.open_frame(self.fd_frame)
                self.update_file_list(conn=conn)
                return
            
            elif 'ERROR' in data:
                # An Error message was declared
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
        self.upload_btn = tk.Button(self.button_frame, text='Upload', width=15,
                                    command=lambda: self.upload_file(conn=conn), bg="#007BFF", fg="white")
        self.upload_btn.grid(row=0, column=0, padx=5, pady=5)
        self.download_btn = tk.Button(self.button_frame, text='Download', width=15,
                                      command=lambda: self.download_file(conn=conn), bg="#28A745", fg="white")
        self.download_btn.grid(row=0, column=1, padx=5, pady=5)
        self.delete_btn = tk.Button(self.button_frame, text='Delete', width=15,
                                    command=lambda: self.delete_file(conn=conn), bg="#DC3545", fg="white")
        self.delete_btn.grid(row=0, column=2, padx=5, pady=5)

        # Add this in setup_fd_frame
        self.create_dir_btn = tk.Button(
        self.button_frame, text='Create Subdirectory', width=15,
            command=lambda: self.create_subdirectory(conn=conn), bg="#6C757D", fg="white"
        )
        self.create_dir_btn.grid(row=0, column=3, padx=5, pady=5)


        # Creates a Listbox to show the list of files
        self.file_listbox = tk.Listbox(self.fd_frame, selectmode=tk.SINGLE, width=70, height=10)
        self.file_listbox.grid(row=3, column=0, pady=10)

        # Refreshes Button to fetch file list
        self.refresh_btn = tk.Button(self.fd_frame, text='Refresh Files', command=lambda: self.update_file_list(conn))
        self.refresh_btn.grid(row=4, column=0, pady=5)


    # Name: setup_au_frame
    # Param: conn - The connection to the server
    # Return: None
    # Desc: Sets up the Authentication frame
    def setup_au_frame(self, conn):
        # Create Authentication frame
        self.au_frame = tk.Frame(self.root, height=self.SIZE_Y, width=self.SIZE_X, padx=20, pady=20, bg='lightgrey')
        self.au_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        # Title for the Authentication process
        self.au_lb1 = tk.Label(self.au_frame, text='Authentication Process', font=('Helvetica', 16, 'bold'), bg='lightgrey')
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
                               bg='#17A2B8', fg='white')
        self.au_b1.grid(row=3, column=0, columnspan=2, padx=10, pady=15)

        # Configure row and column weights for centering
        self.au_frame.grid_rowconfigure(0, weight=1)
        self.au_frame.grid_rowconfigure(4, weight=1)
        self.au_frame.grid_columnconfigure(0, weight=1)
        self.au_frame.grid_columnconfigure(1, weight=1)

    # Name: __init__
    # Param: None
    # Return: None
    # Desc: Sets up the UI for the application upon the creation of a new UI class
    def __init__(self):
        # Sets up connection
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(ADDR)
            print('Connected to server')
        except Exception as e:
            messagebox.showerror('Connection Error', f'Failed to connect to the server: {e}')
            return

        # Setting up root
        self.root = tk.Tk()
        self.root.title('File Transfer Application')

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