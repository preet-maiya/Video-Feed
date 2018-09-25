from helpers import VideoGrabber, SendVideo
import socket 
import os
import numpy as np
import cv2

video_quality = 100
host = "127.0.01" #socket.gethostname()
port = 1080

grabber = VideoGrabber(video_quality)
sender = SendVideo(host, port)

grabber.start()

sender.startTransfer()
while True:
    try:
        buffer = grabber.get_buffer()
        data = buffer.tobytes()
        # print("Buffer size: {}".format(len(data)))
        sender.send(data)

    except KeyboardInterrupt:
        grabber.running = False
        print("Exiting...")
        # grabber.join()
        print(os.getpid())
