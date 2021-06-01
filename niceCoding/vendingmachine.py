import tkinter as tk
from tkinter import messagebox

price = {'coffee':3500, 'latte':4000,'smoothie':4500,'tea':3000}
order = []
sum = 0

window = tk.Tk()
window.title('음료 주문')
window.geometry('300x500')

frame1 = tk.Frame(window)
frame1.pack()

tk.Button(frame1, text='latte',command='',width=10,height=2).grid(row=1, column=0)
tk.Button(frame1, text='latte',command='',width=10,height=2).grid(row=1, column=0)
tk.Button(frame1, text='coffee',command='',width=10,height=2).grid(row=0, column=0)
tk.Button(frame1, text='smoothie',command='',width=10,height=2).grid(row=2, column=0)
tk.Button(frame1, text='tea',command='',width=10,height=2).grid(row=3, column=0)
tk.Button(frame1, text='exit',command='',width=10,height=2).grid(row=4, column=0)

label = tk.Label(window, text='금액: 0원',width=100, height=2,fg='blue')
label.pack()

textarea = tk.Text(window)
textarea.pack()

window.mainloop()