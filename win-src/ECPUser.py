from tkinter import *

class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master
        self.pack(fill=BOTH, expand=1)
        
        text = Label(self, text="Version 1.0 Alpha of the ECP CLI is\n installed on this computer.")
        text.place(x=5,y=5)
        #text.pack()
        
root = Tk()
root.wm_title("ECP 1.0A")
app = Window(root)
root.iconbitmap('icon.ico')
root.geometry("200x50")
root.mainloop()
