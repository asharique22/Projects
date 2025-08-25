import socket

# Create a TCP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
server_address = ('localhost', 12345)
client_socket.connect(server_address)

# Read a line of characters from the keyboard
line = input('Enter a line of characters: ')

# Send the data to the server
client_socket.send(line.encode('utf-8'))

# Receive the modified data from the server and display it
modified_data = client_socket.recv(1024).decode('utf-8')
print('Modified data:', modified_data)

# Close the connection
client_socket.close()
