from Client import Controller
import Tkinter

root = Tkinter.Tk()
controller = Controller(root, '127.0.0.1', "1080", "1000") 
controller.startVideo()  
Tkinter.mainloop()    