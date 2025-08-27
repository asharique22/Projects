import socket
import os

def receive_data(sock):
    header = sock.recv(128).decode('utf-8').strip()
    parts = header.split("|")

    if parts[0] == "TEXT":
        size = int(parts[1])
        data = sock.recv(size).decode('utf-8')
        print("Client sent text:", data)

        # Process and send back uppercase
        response = data.upper()
        sock.sendall(response.encode('utf-8'))
        print("Sent back uppercase:", response)

    elif parts[0] == "FILE":
        size = int(parts[1])
        filename = parts[2]
        print(f"Receiving file: {filename} ({size} bytes)")

        with open("received_" + filename, "wb") as f:
            remaining = size
            while remaining > 0:
                chunk = sock.recv(min(4096, remaining))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)

        print(f"File saved as received_{filename}")

if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(1)
    print("TCP server is waiting for connections...")

    conn, addr = server_socket.accept()
    print("Connection from", addr)

    receive_data(conn)

    conn.close()
    server_socket.close()
