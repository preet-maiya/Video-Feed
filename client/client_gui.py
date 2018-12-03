from Client import Controller
import Tkinter

video_port = 1080
control_port = 1081
command_port = 1000

root = Tkinter.Tk()
controller = Controller(root, '127.0.0.1', video_port, control_port, command_port) 
controller.startVideo()  
root.protocol("WM_DELETE_WINDOW", controller.on_close())
Tkinter.mainloop()    