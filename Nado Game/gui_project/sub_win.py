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