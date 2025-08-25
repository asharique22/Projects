#TCP IS USED

import cv2
import socket
import pickle
import struct

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to a specific address and port
server_address = ('localhost', 5555)
server_socket.bind(server_address)

# Listen for incoming connections
server_socket.listen(5)
print("Server listening on {}:{}".format(*server_address))

# Accept a connection from the client
client_socket, client_address = server_socket.accept()
print("Connection from:", client_address)

# Open the webcam (0 corresponds to the default camera)
cap = cv2.VideoCapture(0)

while True:
    # Read a frame from the webcam
    ret, frame = cap.read()

    # Serialize the frame
    data = pickle.dumps(frame)

    # Pack the serialized frame and send it to the client
    message_size = struct.pack("L", len(data))
    client_socket.sendall(message_size + data)

# Release the webcam and close the connection
cap.release()
client_socket.close()
server_socket.close()
