import socket

# Create a UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to a specific address and port
server_address = ('localhost', 54321)
server_socket.bind(server_address)

print('UDP server is waiting for data...')

# Receive data from the client, convert to uppercase, and send it back
while True:
    data, client_address = server_socket.recvfrom(1024)
    modified_data = data.decode('utf-8').upper()
    server_socket.sendto(modified_data.encode('utf-8'), client_address)
