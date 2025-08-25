import socket

# Create a UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Server address
server_address = ('localhost', 54321)

# Read a line of characters from the keyboard
line = input('Enter a line of characters: ')

# Send the data to the server
client_socket.sendto(line.encode('utf-8'), server_address)

# Receive the modified data from the server and display it
modified_data, _ = client_socket.recvfrom(1024)
print('Modified data:', modified_data.decode('utf-8'))

# Close the connection
client_socket.close()
