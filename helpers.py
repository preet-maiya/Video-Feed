import socket
import cv2
import sys
from threading import Thread, Lock
import sys
import time
import numpy as np

from time import sleep


class VideoGrabber(Thread):
    def __init__(self, jpeg_quality):
        Thread.__init__(self)
        self.encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
        self.cap = cv2.VideoCapture(0)
        self.running = True
        self.buffer = None
        self.lock = Lock()

    def stop(self):
        self.running = False

    def set_quality(self, jpeg_quality):
        self.encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]

    def get_buffer(self):
        if self.buffer is not None:
                self.lock.acquire()
                cpy = self.buffer.copy()
                self.lock.release()
                return cpy
            
    def run(self):
        while self.running:
                success, img = self.cap.read()
                if not success:
                        continue
                
                self.lock.acquire()
                _, self.buffer = cv2.imencode('.jpg', img, self.encode_param)
                self.lock.release()


class SendVideo:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))
        self.operation = ""
        self.seq = -1
        self.max_seq = 1000

    def get_client_address(self):
        while(1):
            self.operation, self.address = self.sock.recvfrom(10)
            print("Client address :{}".format(self.address))
            print(self.operation)

    def startTransfer(self):
        
        #TODO: Move this to a separate thread so the operation can be continued after stopping client
        address_thread = Thread(target=self.get_client_address)
        address_thread.start()
        print("Started a thread for getting client address.")
        sleep(5)
        print(self.address)        

    def send(self, data):
        if self.operation == "get" or True:
            header = ''
            len_data = len(data)
            remaining = len_data
            offset = 65000
            frag_no = 0
            self.seq = (self.seq+1) % self.max_seq
            sequence = "%3d"%self.seq
            # print(sequence)
            # Remaining space after timestamp and one byte to indicate if more comes to be 65490
            while((remaining - offset) > 0):
                ts = "%.5f"%time.time()
                more = '1'
                header = sequence + ts + more
                frag_data = data[frag_no*offset: (frag_no+1)*offset]
                frag_no += 1
                frag_data = header + frag_data
                self.sock.sendto(frag_data, self.address)
                remaining -= offset

            more = '0'
            ts = "%.5f"%time.time()
            header = sequence + ts + more
            frag_data = data[frag_no*offset:]
            frag_data = header + frag_data
            self.sock.sendto(frag_data, self.address)

class ReceiveVideo(Thread):
    def __init__(self, server, port):
        Thread.__init__(self)        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server = server
        self.port = int(port)
        self.lock = Lock()
        self.buffer = cv2.imread('default.jpg', 1)
        self.running = True
        self.delay = []
        self.delay_start = time.time()
        self.prev_seq = 0
        self.end_chars = b'\xff\xd9'

    def setOperation(self, operation="get"):
        server_address = (self.server, self.port)
        self.sock.sendto(operation, server_address)

    def get_frame(self):
        self.lock.acquire()
        copy = self.buffer.copy()
        self.lock.release()
        return copy
        

    def run(self):
        while(self.running):
            seq, more, data = self.revc_data()
            corrupt = 0
            while(more):
                seq_frag, more, tmp = self.revc_data()
                if seq == seq_frag:
                    data += tmp
                else:
                    corrupt = 1
                    break
            
            # TODO: Dirty fix for corrupted image. CORRECT THIS!!!

            end_chars = data[-2:]

            if end_chars != self.end_chars or corrupt:
                continue

            array = np.frombuffer(data, dtype=np.dtype('uint8'))
            # print("{}\t{}".format(self.prev_seq, seq))
            img = cv2.imdecode(array, 1)

            if(type(img) == np.ndarray):
                self.lock.acquire()
                self.buffer = img
                self.lock.release()

    def handle_delay(self, delay):
        self.delay.append(delay)

        if (time.time() - self.delay_start) > 5:
            self.delay_start = time.time()
            self.delay = [] 
        
    def get_delay(self):
        ndelay = len(self.delay)
        ret_val = sum(self.delay)/float(ndelay)
        self.delay_start = time.time()
        self.delay = []
        return ret_val

    def revc_data(self):
        data, _ = self.sock.recvfrom(65020)
        ts = time.time()
        if len(data) == 4:
            if(data == "FAIL"):
                return None

        header = data[:20]
        data = data[20:]

        seq = int(header[:3])

        ts_recv = float(header[3:19])
        delay = ts - ts_recv
        self.handle_delay(delay)

        more = int(header[19])
        
        return (seq, more, data)

class SendCommands:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))
        self.host = host
        self.port = port
        self.server_address = (host, int(port))

    def sendCommand(self, msg):
        self.sock.sendto(msg, self.server_address)
