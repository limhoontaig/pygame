# import tkinter as tk

# class MainWindow(tk.Frame):
#     counter = 0
#     def __init__(self, *args, **kwargs):
#         tk.Frame.__init__(self, *args, **kwargs)
#         self.button = tk.Button(self, text="Create new window", 
#                                 command=self.create_window)
#         self.button.pack(side="top")

#     def create_window(self):
#         self.counter += 1
#         t = tk.Toplevel(self)
#         t.wm_title("Window #%s" % self.counter)
#         l = tk.Label(t, text="This is window #%s" % self.counter)
#         l.pack(side="top", fill="both", expand=True, padx=100, pady=100)

# if __name__ == "__main__":
#     root = tk.Tk()
#     main = MainWindow(root)
#     main.pack(side="top", fill="both", expand=True)
#     root.mainloop()




import tkinter as tk
from tkinter import ttk
class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        top = self.winfo_toplevel()
        self.menuBar = tk.Menu(top)
        top['menu'] = self.menuBar
        self.menuBar.add_command(label='Child1', command=self.__create_child1)
        self.menuBar.add_command(label='Child2', command=lambda: self.__create_child2(True))
        self.TestLabel = ttk.Label(self, text='Use the buttons from the toplevel menu.')
        self.TestLabel.pack()
        self.__create_child2(False)

    def __create_child1(self):
        self.Child1Window = tk.Toplevel(master=self, width=100, height=100)
        self.Child1WindowButton = ttk.Button(self.Child1Window, text='Focus Child2 window else create Child2 window', command=self.CheckForChild2)
        self.Child1WindowButton.pack()

    def __create_child2(self, givenarg):
        self.Child2Window = tk.Toplevel(master=self, width=100, height=100)
        if givenarg == False:
            self.Child2Window.withdraw()
            # Init some vars or widgets
            self.Child2Window = None
        else:
            self.Child2Window.TestLabel = ttk.Label(self.Child2Window, text='This is Child 2')
            self.Child2Window.TestLabel.pack()

    def CheckForChild2(self):
        if self.Child2Window:
            if self.Child2Window.winfo_exists():
                self.Child2Window.focus()
            else:
                self.__create_child2(True)
        else:
            self.__create_child2(True)

if __name__ == '__main__':
    App().mainloop()

# https://www.plus2net.com/python/tkinter-Toplevel.php



import tkinter as tk
from tkinter import * 

my_w = tk.Tk()
my_w.geometry("200x200")  # Size of the window 
my_w.title("www.plus2net.com")  # Adding a title

# create one lebel 
my_str = tk.StringVar()
l1 = tk.Label(my_w,  textvariable=my_str )
l1.grid(row=1,column=2) 
my_str.set("Hi I am main window")

# child window 
my_w_child=Toplevel(my_w) # Child window 
my_w_child.geometry("200x200")  # Size of the window 
my_w_child.title("www.plus2net.com")

my_str1 = tk.StringVar()
l1 = tk.Label(my_w_child,  textvariable=my_str1 )
l1.grid(row=1,column=2) 
my_str1.set("Hi I am Child window")

my_w.mainloop()





import tkinter as tk
from tkinter import * 
my_w = tk.Tk()
my_w.geometry("200x200")  # Size of the window 
my_w.title("www.plus2net.com")  # Adding a title

# create one lebel 
my_str = tk.StringVar()
l1 = tk.Label(my_w,  textvariable=my_str )
l1.grid(row=1,column=2) 
my_str.set("Hi I am main window")
# add one button 
b1 = tk.Button(my_w, text='Clik me to open new window',
               command=lambda:my_open())
b1.grid(row=2,column=2) 

def my_open():
    my_w_child=Toplevel(my_w) # Child window 
    my_w_child.geometry("200x200")  # Size of the window 
    my_w_child.title("www.plus2net.com")

    my_str1 = tk.StringVar()
    l1 = tk.Label(my_w_child,  textvariable=my_str1 )
    l1.grid(row=1,column=2) 
    my_str1.set("Hi I am Child window")
my_w.mainloop()




import tkinter as tk
from tkinter import * 
my_w = tk.Tk()
my_w.geometry("200x200")  # Size of the window 
my_w.title("www.plus2net.com")  # Adding a title

# create one lebel 
my_str = tk.StringVar()
l1 = tk.Label(my_w,  textvariable=my_str )
l1.grid(row=1,column=2) 
my_str.set("Hi I am main window")
# add one button 
b1 = tk.Button(my_w, text='Clik me to open new window',
               command=lambda:my_open())
b1.grid(row=2,column=2) 

def my_open():
    my_w_child=Toplevel(my_w) # Child window 
    my_w_child.geometry("200x200")  # Size of the window 
    my_w_child.title("www.plus2net.com")

    my_str1 = tk.StringVar()
    l1 = tk.Label(my_w_child,  textvariable=my_str1 )
    l1.grid(row=1,column=2) 
    my_str1.set("Hi I am Child window")
    b2 = tk.Button(my_w_child, text=' Close parent',
                   command=my_w.destroy)
    b2.grid(row=2,column=2) 

    b3 = tk.Button(my_w_child, text=' Close Child',
                   command=my_w_child.destroy)
    b3.grid(row=3,column=2)

    b4 = tk.Button(my_w_child, text='Red',
        command=lambda:my_w_child.config(bg='red'))
    # change background color of parent from child
    b4 = tk.Button(my_w_child, text='Parent Colour',
		command=lambda:my_w.config(bg='red'))
    b4.grid(row=4,column=2)
    
    # change background color of child from parent 
    b5 = tk.Button(my_w, text='Child Colour',
		command=lambda:my_w_child.config(bg='green'))
    b5.grid(row=5,column=2)


my_w.mainloop()


