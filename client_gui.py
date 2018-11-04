import Tkinter
import tkMessageBox
from Tkinter import E, Frame, Canvas, PhotoImage, NW, S
import PIL.ImageTk
from helpers import ReceiveVideo, SendCommands
import cv2
import numpy as np


class Controller:
    def __init__(self, root, host, video_port, command_port):
        self.receiver = ReceiveVideo(host, video_port)
        self.sendCommands = SendCommands(host, command_port)
        
        self.receiver.start()
        self.receiver.setOperation()

        self.root = root

        self.buttons = Frame(root)
        self.buttons.pack()

        self.display = Frame(root)
        self.display.pack()

        self.canvas = Canvas(self.display, width = 480, height = 640)      
        self.canvas.pack()      
        self.img = PhotoImage(file="default.png")      
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

        self.root.geometry("500x500")
       
        self.delay = 50
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



root = Tkinter.Tk()
controller = Controller(root, '127.0.0.1', "1080", "1000") 
controller.startVideo()  
Tkinter.mainloop()    