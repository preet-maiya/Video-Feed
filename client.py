import socket
import cv2
import numpy as np
import sys
import time
from helpers import ReceiveVideo


if(len(sys.argv) != 3):
    print("Usage : {} hostname port".format(sys.argv[0]))
    print("e.g.   {} 192.168.0.39 1080".format(sys.argv[0]))
    sys.exit(-1)


# cv2.namedWindow("Feed")

receiver = ReceiveVideo(sys.argv[1], sys.argv[2])
receiver.start()
receiver.setOperation()

while(True):
    try:
        frame = receiver.get_frame()
        # print("Fragment size : {}".format(len(frame)))
        
        cv2.imshow("Feed", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if cv2.waitKey(1) & 0xFF == ord('d'):
            print("Average delay: {}".format(receiver.get_delay()))
    except KeyboardInterrupt:
        sys.exit()