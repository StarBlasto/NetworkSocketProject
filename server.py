# [SERVER]
# Imported modules
import os
import socket
import threading
import hashlib
import time
import datetime
import shutil
from analysis import start_track, end_track, report
from tqdm import tqdm


# Constant Variables
IP = '10.180.80.204'
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = 'utf-8'
SERVER_DATA_PATH = 'server_data'

# Password Info
correct_password = "password123"
correct_password_hashed = hashlib.sha256(correct_password.encode()).hexdigest()


# Name: current_time
# Param: None
# Return: (str) - The current time in formatted string
# Desc: Provides the string to the current time of the function call
def current_time():
    now = datetime.datetime.now()
    formmated_now = now.strftime('%Y-%m-%d %H:%M:%S')
    return formmated_now

# Name: autheticate_conn
# Param1: conn - the connection made
# Return: True or False
# Desc: Verifies whether a user should or shouldn't be on this connection
def autheticate_conn(conn):
    # Handles initial verification
    conn.send('OK@Username:'.encode(FORMAT))
    username = conn.recv(SIZE).decode(FORMAT)
    conn.send('OK@Password:'.encode(FORMAT))
    password = conn.recv(SIZE).decode(FORMAT)
    print(f'Server: Recieved hashed password: {password}')

    # Completes final verification
    if username == 'user' and password == correct_password_hashed:
        conn.send('OK@Permission verified'.encode(FORMAT))
        print(f'Permission Verified')  
        return True
    else:
        conn.send('ERROR@Permission denied'.encode(FORMAT))
        print(f'Permission Denied')
        return False

# Name: handle_conn
# Param1: conn - the connection
# Param2: addr - the address
# Return: None
# Desc: Handles the created connection
def handle_conn(conn, addr):
    print(f'NEW CONNECTION: {addr} connected')

    # Handles authentication
    if not autheticate_conn(conn):
        conn.close()
        return
    
    # Continues looping
    while True:
        try:
            # Gathers data from client
            data = conn.recv(SIZE).decode(FORMAT)
            if not data:
                break

            # Splits data
            cmd = data.split(' ')[0]

            if cmd == 'UPLOAD':
                print(f'{addr} has called the UPLOAD command')
                # --------------------------------------------------------------------------------------
                # | UPLOAD | command
                # Sets up file path
                file_path = conn.recv(SIZE).decode(FORMAT).strip("/")
                full_path = os.path.join(SERVER_DATA_PATH, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                # Checks if file already exists
                if os.path.exists(full_path):
                    conn.send('ALREADY EXISTS'.encode(FORMAT))
                    print('File already exists')
                else:
                    conn.send('DOESNT EXIST'.encode(FORMAT))
                    print('File doesnt already exist')

                # Client response
                client_resp = conn.recv(SIZE).decode(FORMAT)
                if client_resp == 'NO':
                    continue
                
                # Starts tracking
                start_track(addr)
                
                # Sends file
                print('Start file transfer')
                with open(full_path, 'wb') as opened_file:
                    while True:
                        chunk = conn.recv(SIZE)
                        if chunk == b'EOF':
                            print('EOF Located')
                            break
                        opened_file.write(chunk)
                conn.send('FILE UPLOADED'.encode(FORMAT))
                print('Finished file transfer')

                # Handles file size and speed
                file_size = os.path.getsize(full_path)
                file_size_int = int(file_size)
                upload_speed = end_track(addr, file_size_int)
                report(msg=f'{addr} | UPLOADED File (To Server): {file_path} | Time: {current_time()}\nFile Size: {round(file_size/(1024*1024), 2)} MB | Upload Speed: {upload_speed} MB/s\n\n')
                print(f'{addr} uploaded {file_path} to the server.')

                # Sends the upload speed
                conn.send(f'{upload_speed}'.encode(FORMAT))
                pass

            elif cmd == 'DOWNLOAD':
                # --------------------------------------------------------------------------------------
                # | DOWNLOAD | command
                try:
                    # Receives the file name from client request
                    file_name = conn.recv(SIZE).decode(FORMAT).strip()
                    file_path = os.path.join(SERVER_DATA_PATH, file_name)

                    # Check if the file exists
                    if not os.path.exists(file_path):
                        error_message = f'ERROR@File {file_name} does not exist.'
                        conn.send(error_message.encode(FORMAT))
                        print(f'Download request failed: {error_message}')
                        return
                    
                    # Starts tracking
                    start_track(addr)

                    # Handles file size
                    file_size = os.path.getsize(file_path)
                    file_size_int = int(file_size)
                    progress_bar = tqdm(total=file_size_int, unit='iB', unit_scale=True)

                    # Open and send the file in chunks
                    with open(file_path, 'rb') as f:
                        print(f'Sending {file_name} to client...')
                        while chunk := f.read(SIZE):
                            if chunk.startswith(b'CMD:'):
                                command = chunk[4:].decode('utf-8')
                                print(f'Received Command: {command}')
                            else:
                                #print(f'Sending chunk: {chunk[:50]}...')
                                conn.send(chunk)
                                progress_bar.update(len(chunk))
                
                    # Handles upload speed
                    download_speed = end_track(addr, file_size_int)
                    report(msg=f'{addr} | DOWNLOADED File (From Server): {file_path} | Time: {current_time()}\nFile Size: {round(file_size/(1024*1024), 2)} MB | Download Speed: {download_speed} MB/s\n\n')

                    # Send an EOF to indicate the end of the file transfer
                    conn.send(b'EOF')
                    print(f'Finished sending {file_name}.')

                    # Getting confirmation
                    conn.recv(SIZE).decode(FORMAT)

                    # Sends the download speed
                    conn.send(f'{download_speed}'.encode(FORMAT))

                except Exception as e:
                    # Handles any exception during download
                    error_message = f"ERROR@{str(e)}"
                    conn.send(error_message.encode(FORMAT))
                    print(f"Error during file download: {error_message}")

            # Server code to handle DELETE command
            elif cmd == 'DELETE':
                # --------------------------------------------------------------------------------------
                # | DELETE | command
                # Receive the item path from the client
                o_path = conn.recv(SIZE).decode(FORMAT)
                item_path = os.path.join(SERVER_DATA_PATH, o_path)

                try:
                    if os.path.isfile(item_path):
                        # Delete file
                        report(msg=f'{addr} | DELETED File (From Server): {o_path} | Time: {current_time()}\nFile Size: {round(os.path.getsize(item_path)/(1024*1024),2)} MB\n\n')
                        os.remove(item_path)
                        conn.send("FILE_DELETED".encode(FORMAT))
                        print(f"File '{item_path}' deleted successfully.")
                    elif os.path.isdir(item_path):
                        # Delete directory and its contents
                        report(msg=f'{addr} | DELETED Directory (From Server): {o_path} | Time: {current_time()}\n\n')
                        shutil.rmtree(item_path)
                        conn.send("FILE_DELETED".encode(FORMAT))
                        print(f"Directory '{item_path}' deleted successfully.")
                    else:
                        conn.send("ERROR@Item does not exist.".encode(FORMAT))
                except Exception as e:
                    # Send error message to the client
                    error_message = f"ERROR@{str(e)}"
                    conn.send(error_message.encode(FORMAT))
                    print(f"Failed to delete '{item_path}': {e}")

            elif cmd == 'DIR':
                # --------------------------------------------------------------------------------------
                # | DIR | command
                print('Server requested DIR')
                def list_files(directory, path=""):
                    result = []
                    for item in os.listdir(directory):
                        item_path = os.path.join(directory, item)
                        if os.path.isdir(item_path):
                            result.append(f"{path}{item}/")
                            result.extend(list_files(item_path, f"{path}{item}/"))
                        else:
                            result.append(f"{path}{item}")
                    return result
                
                files = list_files(SERVER_DATA_PATH)
                files_list = "\n".join(files) if files else "Empty"
                conn.send(files_list.encode(FORMAT))

            elif cmd == 'LOGOUT':
                # --------------------------------------------------------------------------------------
                # | LOGOUT | command
                print(f'{addr} requests logout')
                break

            elif cmd == 'CREATE_DIR':
                # --------------------------------------------------------------------------------------
                # | CREATE_DIR | command
                print('Server requested to create directory')
                try:
                    dir_name = conn.recv(SIZE).decode(FORMAT)
                    new_dir_path = os.path.join(SERVER_DATA_PATH, dir_name)
                    os.makedirs(new_dir_path, exist_ok=True)
                    conn.send("DIR_CREATED".encode(FORMAT))
                    print(f"Directory '{dir_name}' created successfully.")
                except Exception as e:
                    conn.send(f"ERROR@{str(e)}".encode(FORMAT))
                    print(f"Failed to create directory '{dir_name}': {e}")

            else:
                conn.send('ERROR@Invalid Command'.encode(FORMAT))
        except Exception as e:
            print(f'Error: {e}')
            break
    print(f'{addr} disconnected')
    conn.close()

# Name: main
# Param: None
# Return: None
# Desc: Handles connecting to a server (We're the Client)
def main():
    if not os.path.exists(SERVER_DATA_PATH):
        os.makedirs(SERVER_DATA_PATH)

    # Sets up connection
    print('Starting the server...')
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print(f'Server is listening on {IP}:{PORT}')

    # Core loop of the program
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_conn, args=(conn, addr))
        thread.start()
        print(f'ACTIVE CONNECTIONS: {threading.active_count() - 1}')


# runs main
if __name__ == '__main__':
    main()