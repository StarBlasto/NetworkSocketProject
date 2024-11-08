# [SERVER]
# Imported modules
import os
import socket
import threading
import hashlib
import time

# Constant Variables
IP = 'localhost' ### gethostname()
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = 'utf-8'
SERVER_DATA_PATH = 'server_data'

# Password Info
correct_password = "password123"
correct_password_hashed = hashlib.sha256(correct_password.encode()).hexdigest()

# Name: autheticate_conn
# Param1: conn - the connection made
# Return: True or False
# Desc: Verifies whether a user should or shouldn't be on this connection
def autheticate_conn(conn):
    conn.send('OK@Username:'.encode(FORMAT))
    username = conn.recv(SIZE).decode(FORMAT)
    conn.send('OK@Password:'.encode(FORMAT))
    password = conn.recv(SIZE).decode(FORMAT)
    print(f'Server: Recieved hashed password: {password}')

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
                # UPLOAD command
                # Sets up file path
                file_name = conn.recv(SIZE).decode(FORMAT)
                file = os.path.join(SERVER_DATA_PATH, file_name)

                # Opens file
                with open(file, 'wb') as opened_file:

                    # Loops and adds chunks until final bit chunk
                    while True:
                        chunk = conn.recv(SIZE)
                        if chunk == b'EOF':
                            break
                        opened_file.write(chunk)

                # Finishes confirmation message
                print(f'{addr} upploaded {file_name} to the server')  
                conn.send('FILE UPLOADED'.encode(FORMAT))
                pass

            elif cmd == 'DOWNLOAD':
                try:
                    # Receives the file from client side
                    file_name = conn.recv(SIZE).decode(FORMAT)
                    file_path = os.path.join(SERVER_DATA_PATH, file_name)

                    # Check if the file exists
                    if not os.path.exists(file_path):
                        conn.send(f"ERROR@File {file_name} does not exist.".encode(FORMAT))
                        return

                    # Open and send the file in chunks
                    with open(file_path, "rb") as f:
                        print(f"Sending {file_name} to client...")
                        while chunk := f.read(SIZE):
                            conn.send(chunk)
                    conn.send(b"EOF")
                    print(f"Finished sending {file_name}.")

                except Exception as e:
                    # Handles exception error
                    print(f"Error during file download: {e}")

            elif cmd == 'DELETE':
                print(f'{addr} requests deleting file')
                pass
            elif cmd == 'DIR':
                pass
            elif cmd == 'LOGOUT':
                print(f'{addr} requests logout')
                break
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

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_conn, args=(conn, addr))
        thread.start()
        print(f'ACTIVE CONNECTIONS: {threading.active_count() - 1}')


# runs main
if __name__ == '__main__':
    main()