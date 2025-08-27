import socket
import os

def send_text(sock, message):
    data = message.encode('utf-8')
    header = f"TEXT|{len(data)}".encode('utf-8').ljust(128)
    sock.sendall(header + data)

    # Receive server response (uppercase)
    response = sock.recv(4096).decode('utf-8')
    print("Server replied:", response)

def send_file(sock, filepath):
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    header = f"FILE|{filesize}|{filename}".encode('utf-8').ljust(128)
    sock.sendall(header)

    with open(filepath, "rb") as f:
        while chunk := f.read(4096):
            sock.sendall(chunk)

    print(f"File '{filename}' sent successfully!")

if __name__ == "__main__":
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 12345))

    choice = input("Send text (t) or file (f)? ")

    if choice.lower() == "t":
        msg = input("Enter your message: ")
        send_text(client_socket, msg)

    elif choice.lower() == "f":
        path = input("Enter file path: ")
        if os.path.exists(path):
            send_file(client_socket, path)
        else:
            print("File not found!")

    client_socket.close()
