from Client import Controller
import Tkinter

video_port = 1080
command_port = 1000

root = Tkinter.Tk()
controller = Controller(root, '127.0.0.1', video_port, command_port) 
controller.startVideo()  
Tkinter.mainloop()    