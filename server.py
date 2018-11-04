from helpers import VideoGrabber, SendVideo, GetCommands
import socket 
import os
import numpy as np
import cv2
from threading import Thread


video_quality = 60
host = "127.0.0.1" #socket.gethostname()
video_port = 1080
command_port = 1000

grabber = VideoGrabber(video_quality)
sender = SendVideo(host, video_port)
receiver = GetCommands(host, command_port)

grabber.start()

sender.startTransfer()
client, client_address = receiver.sock.accept()
client_handler = Thread(
    target=receiver.handle_client_connection,
    args=(client,)  # without comma you'd get a... TypeError: handle_client_connection() argument after * must be a sequence, not _socketobject
)
client_handler.start()
while True:
    try:
        buffer = grabber.get_buffer()
        data = buffer.tobytes()
        # if receiver.message is not None :
        #     print(receiver.message)
        # print("Buffer size: {}".format(len(data)))
        sender.send(data)

    except KeyboardInterrupt:
        grabber.running = False
        print("Exiting...")
        # grabber.join()
        print(os.getpid())
