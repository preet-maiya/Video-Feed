from threading import Thread, Lock
import time
import cv2
import socket


class VideoGrabber(Thread):
    def __init__(self, jpeg_quality):
        Thread.__init__(self)
        self.encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
        self.cap = cv2.VideoCapture(0)
        self.running = True
        self.buffer = None
        self.lock = Lock()
        self.buffer = cv2.imread("../resources/default.png")

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


class SendVideo(Thread):
    def __init__(self, host, port, jpeg_quality):
        Thread.__init__(self)        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, int(port)))
        self.operation = ""
        self.seq = -1
        self.max_seq = 1000
        self.grabber = VideoGrabber(jpeg_quality)

    def get_control_data(self):
        while(1):
            data, address = self.sock.recvfrom(10)
            self.handle_data((data, address))
           
    def handle_data(self, data):
        _data = data[0]
        _address = data[1]

        t = int(_data[0])
        _data = _data[1:]

        if t==0:
            print("Client address :{}".format(self.address))
            self.operation = _data
            self.address = _address
            print(self.operation)

        elif t==1:
            print("Changed quality to {}".format(_data))
            _data = int(_data)
            self.grabber.set_quality(_data)
            
    def startTransfer(self):
        
        #TODO: Dirty fix for the first connection. Correct this.
        data, self.address = self.sock.recvfrom(10)
        self.operation = data[1:]

        address_thread = Thread(target=self.get_control_data)
        address_thread.start()
        print("Started a thread for getting client address.")
        print(self.address)
        
        self.running = True

        print("Started camera.")
        self.grabber.start()

    def sendFrame(self, data):
        if self.operation == "get" or True:
            header = ''
            len_data = len(data)
            remaining = len_data
            offset = 65000
            frag_no = 0
            self.seq = (self.seq+1) % self.max_seq
            sequence = "%3d"%self.seq

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

    def run(self):
        self.startTransfer()
        while self.running:
            buffer = self.grabber.get_buffer()
            data = buffer.tobytes()
            self.sendFrame(data)

class GetCommands(Thread):
    def __init__(self, host, port):
        Thread.__init__(self)        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = int(port)
        self.sock.bind((host, self.port))
        self.sock.listen(5)

    def get_client_connection(self):
        while(True):
            self.client_sock, self.client_addr = self.sock.accept()
            print("New client {}".format(self.client_addr))

    def set_client(self):
        print("Waiting for client connection...")
        self.client_sock, self.client_addr = self.sock.accept()
        client_connection_thread = Thread(target=self.get_client_connection)
        client_connection_thread.start()
        print("Started client connection thread.")

    def run(self):
        self.set_client()
        while True :
            self.message = self.client_sock.recv(1024)
            print(self.message)
