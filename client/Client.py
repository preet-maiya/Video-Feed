import Tkinter
import tkMessageBox
from Tkinter import E, Frame, Canvas, PhotoImage, NW, S, Scale, HORIZONTAL, W, LEFT, RIGHT
import PIL.ImageTk
import cv2
import numpy as np
import socket
from threading import Thread, Lock
import time


class ReceiveVideo(Thread):
    def __init__(self, server, video_port, control_port):
        Thread.__init__(self)        
        self.video_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server
        self.video_port = int(video_port)
        self.control_port = int(control_port)

        self.lock = Lock()
        self.buffer = cv2.imread("../resources/default.png", 1)
        self.running = True
        self.delay = []
        self.delay_start = time.time()
        self.prev_seq = 0
        self.end_chars = b'\xff\xd9'
        self.server_address_video = (self.server, self.video_port)
        self.server_address_control = (self.server, self.control_port)

        self.control_sock.connect(self.server_address_control)

        self.video_sock.bind(('', 0))
        # self.control_sock.listen(5)

    def setOperation(self, operation="get"):
        data = "0" + operation
        sock_name = str(self.video_sock.getsockname())
        data += "~" + sock_name
        print(data)
        self.control_sock.send(data)

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
        data, _ = self.video_sock.recvfrom(65020)
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

        self.control_sock.send(data)
        print("Changed quality to {}".format(quality))

    def update_auto_mode(self, auto):
        auto = str(auto)
        data = "2" + auto
        
        self.control_sock.send(data)
        print("Updated auto mode to {}".format(bool(int(auto))))

    def close(self):
        data = "3close"
        self.control_socl.send(data)
        self.control_sock.close()
        self.video_sock.close()

class SendCommands:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = int(port)
        self.sock.connect((self.host, self.port))

    def sendCommand(self, msg):
        self.sock.send(msg)


class Controller:
    def __init__(self, root, host, video_port, control_port, command_port):
        self.receiver = ReceiveVideo(host, video_port, control_port)
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
        self.scale.set(self.quality)
        self.scale.bind("<ButtonRelease-1>", self.set_quality)
        self.scale.pack(pady=30)

        init_frame  = self.receiver.get_frame()
        print(init_frame.shape)
        l, b, _ = init_frame.shape
        self.canvas = Canvas(self.display, width = 1.8*l, height = b)      
        self.canvas.pack()      
        self.img = PhotoImage(file="../resources/default.png")      
        self.canvas.create_image(20,20, anchor=NW, image=self.img)
            
        self.forward = Tkinter.Button(self.buttons, text ="Forward", command = self.upFunc)
        self.backward =  Tkinter.Button(self.buttons, text ="Backward", command = self.downFunc)
        self.left =  Tkinter.Button(self.buttons, text ="Left", command = self.leftFunc)
        self.right =  Tkinter.Button(self.buttons, text ="Right", command = self.rightFunc)

        self.autonomous = Frame(self.controls)
        self.autonomous.pack(pady=10)
        self.auto_button = Tkinter.Button(self.autonomous, text="OFF", bg="Red", anchor=E, command=self.toggle_auto)
        self.toggle = False
        self.auto_label = Tkinter.Label(self.autonomous, text="Autonomous mode:", anchor=W)

        self.auto_button.pack(side=RIGHT)
        self.auto_label.pack(side=LEFT)
        

        self.forward.grid(row=0, column=1)
        self.backward.grid(row=2, column=1)
        self.left.grid(row=1, column=0)
        self.right.grid(row=1, column=2)

        self.root.bind('<Up>', self.upFunc)
        self.root.bind('<Down>', self.downFunc)
        self.root.bind('<Right>', self.rightFunc)
        self.root.bind('<Left>', self.leftFunc)

        self.root.geometry("500x850")
       
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

    def toggle_auto(self):
        if self.toggle:
            self.auto_button.config(bg="Red", text="OFF")
            data = 0
            self.receiver.update_auto_mode(data)
        else:
            self.auto_button.config(bg="Green", text="ON")
            data = 1
            self.receiver.update_auto_mode(data)

        self.toggle = not self.toggle  

        print(self.root.winfo_height())

    def on_close(self):
        self.receiver.close()

