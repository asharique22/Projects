import socket

# Create a TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to a specific address and port
server_address = ('localhost', 12345)
server_socket.bind(server_address)

# Listen for incoming connections
server_socket.listen(1)

print('TCP server is waiting for connections...')

# Accept a connection
client_socket, client_address = server_socket.accept()
print('Connection from', client_address)

# Receive data from the client, convert to uppercase, and send it back
while True:
    data = client_socket.recv(1024).decode('utf-8')
    if not data:
        break
    modified_data = data.upper()
    client_socket.send(modified_data.encode('utf-8'))

# Close the connection
client_socket.close()
server_socket.close()
