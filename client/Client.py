import Tkinter
import tkMessageBox
from Tkinter import E, Frame, Canvas, PhotoImage, NW, S, Scale, HORIZONTAL
import PIL.ImageTk
import cv2
import numpy as np
import socket
from threading import Thread, Lock
import time


class ReceiveVideo(Thread):
    def __init__(self, server, port):
        Thread.__init__(self)        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server = server
        self.port = int(port)
        self.lock = Lock()
        self.buffer = cv2.imread("../resources/default.png", 1)
        self.running = True
        self.delay = []
        self.delay_start = time.time()
        self.prev_seq = 0
        self.end_chars = b'\xff\xd9'
        self.server_address = (self.server, self.port)

    def setOperation(self, operation="get"):
        data = "0" + operation
        self.sock.sendto(data, self.server_address)

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

    def update_quality(self, quality):
        quality = str(quality)
        data = "1" + quality
        self.sock.sendto(data, self.server_address)
        print("Changed quality to {}".format(quality))

class SendCommands:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = int(port)
        self.sock.connect((self.host, self.port))

    def sendCommand(self, msg):
        self.sock.send(msg)


class Controller:
    def __init__(self, root, host, video_port, command_port):
        self.receiver = ReceiveVideo(host, video_port)
        self.sendCommands = SendCommands(host, command_port)

        self.receiver.start()
        self.receiver.setOperation()

        self.root = root

        self.display = Frame(root)
        self.display.pack()

        self.controls = Frame(root)
        self.controls.pack()

        self.buttons = Frame(self.controls)
        self.buttons.pack()

        self.quality = 50
        self.step = 5
        self.scale = Scale(self.controls, variable=self.quality, orient=HORIZONTAL, length=200)
        self.scale.bind("<ButtonRelease-1>", self.set_quality)

        self.scale.pack()
        init_frame  = self.receiver.get_frame()
        l, b, _ = init_frame.shape
        self.canvas = Canvas(self.display, width = l, height = b-100)      
        self.canvas.pack()      
        self.img = PhotoImage(file="../resources/default.png")      
        self.canvas.create_image(20,20, anchor=NW, image=self.img)      
            
        self.forward = Tkinter.Button(self.buttons, text ="Forward", command = self.upFunc)
        self.backward =  Tkinter.Button(self.buttons, text ="Backward", command = self.downFunc)
        self.left =  Tkinter.Button(self.buttons, text ="Left", command = self.leftFunc)
        self.right =  Tkinter.Button(self.buttons, text ="Right", command = self.rightFunc)

        self.forward.grid(row=0, column=1)
        self.backward.grid(row=2, column=1)
        self.left.grid(row=1, column=0)
        self.right.grid(row=1, column=2)

        self.root.bind('<Up>', self.upFunc)
        self.root.bind('<Down>', self.downFunc)
        self.root.bind('<Right>', self.rightFunc)
        self.root.bind('<Left>', self.leftFunc)

        self.root.geometry("500x750")
       
        self.delay = 1
        self.startVideo()

        self.root.mainloop()


    def upFunc(self, event=None):
        print("Up")
        self.sendCommands.sendCommand("up")

    def downFunc(self, event=None):
        print("Down")
        self.sendCommands.sendCommand("down")

    def leftFunc(self, event=None):
        print("Left")
        self.sendCommands.sendCommand("left")

    def rightFunc(self, Event=None):
        print("Right")
        self.sendCommands.sendCommand("right")

    def startVideo(self):
        frame = self.receiver.get_frame()
        frame = frame[...,[2,1,0]]
        self.video_frame = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
        self.canvas.create_image(0, 0, image=self.video_frame, anchor=NW)
        self.root.after(self.delay, self.startVideo)

    def set_quality(self, event):
        quality = int(self.scale.get())
        print(self.scale.get())
        mod_val = quality % self.step

        if mod_val > self.step/2:
            quality = quality + (self.step-mod_val)
        else:
            quality = quality - mod_val

        self.scale.set(quality)

        if self.quality == quality:
            return

        self.quality = quality

        print(self.quality)
        self.receiver.update_quality(quality)
