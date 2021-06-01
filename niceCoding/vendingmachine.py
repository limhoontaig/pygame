import tkinter as tk
from tkinter import messagebox

price = {'coffee':3500, 'latte':4000,'smoothie':4500,'tea':3000}
order = []
sum = 0


def add(item):
    global sum

    if item not in price:
        # label1['text'] ='No Drink'
        textarea.insert(tk.INSERT, 'No drink ')
        

    this_price = price.get(item)
    sum += this_price
    order.append(item)
    textarea.insert(tk.INSERT, item+' ')
    label1['text'] = '금액: '+str(sum) + '원'


def btn_exit():
    msgbox = tk.messagebox.askquestion('확인', '주문을 마치겠습니까?')
    if msgbox == 'yes':
        exit()


window = tk.Tk()
window.title('음료 주문')
window.geometry('300x500+500+50')

frame1 = tk.Frame(window)
frame1.pack()


tk.Button(frame1, text='coffee',command=lambda: add('coffee'),width=10,height=2).grid(row=0, column=0)
tk.Button(frame1, text='latte',command=lambda: add('latte'),width=10,height=2).grid(row=1, column=0)
tk.Button(frame1, text='smoothie',command=lambda: add('smoothie'),width=10,height=2).grid(row=2, column=0)
tk.Button(frame1, text='tea',command=lambda: add('tea'),width=10,height=2).grid(row=3, column=0)
tk.Button(frame1, text='red tea',command=lambda: add('red tea'),width=10,height=2).grid(row=4, column=0)
tk.Button(frame1, text='exit',command=btn_exit,width=10,height=2).grid(row=5, column=0)

label1 = tk.Label(window, text='금액: 0원',width=100, height=2,fg='blue')
label1.pack()

textarea = tk.Text(window)
textarea.pack()

window.mainloop()
