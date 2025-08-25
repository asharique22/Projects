#TCP IS USED

import cv2
import socket
import pickle
import struct

# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
server_address = ('localhost', 5555)
client_socket.connect(server_address)
print("Connected to {}:{}".format(*server_address))

# Receive video frames and display them
data = b""
payload_size = struct.calcsize("L")

while True:
    # Receive the size of the frame
    while len(data) < payload_size:
        packet = client_socket.recv(4)
        if not packet:
            break
        data += packet

    # Break the loop if there's no more data
    if not data:
        break

    # Unpack the frame size and receive the frame data
    packed_size = data[:payload_size]
    data = data[payload_size:]
    frame_size = struct.unpack("L", packed_size)[0]

    # Receive the frame data
    while len(data) < frame_size:
        data += client_socket.recv(4096)

    # Extract the frame and display it
    frame_data = data[:frame_size]
    data = data[frame_size:]
    frame = pickle.loads(frame_data)

    # Display the frame
    cv2.imshow('Video Stream', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Close the connection and destroy the OpenCV window
client_socket.close()
cv2.destroyAllWindows()
