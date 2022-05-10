import tkinter as tk
from tkinter import messagebox

price = {'coffee':3500, 'latte':4000,'smoothie':4500,'tea':3000, 'red tea':3200}
order = []
sum = 0
coffee_count = 0
latte_count = 0
smoothie_count = 0
tea_count = 0
red_tea_count = 0


def add(item):
    global sum

    if item not in price:
        # label1['text'] ='No Drink'
        textarea.insert(tk.INSERT, 'No drink ')
        

    this_price = price.get(item)
    sum += this_price
    count(item)
    order.append(item)
    textarea.insert(tk.INSERT, item+' ')
    label1['text'] = '금액: '+str(sum) + '원'

def cancel(item):
    global sum

    if item not in price:
        # label1['text'] ='No Drink'
        textarea.insert(tk.INSERT, 'No drink ')

    if item not in order:
        return
        

    this_price = price.get(item)
    sum -= this_price
    count(item)
    order.remove(item)
    textarea.insert(tk.INSERT, '-'+item+' ')
    label1['text'] = '금액: '+str(sum) + '원'

def count(item):
    global coffee_count
    global latte_count
    global smoothie_count
    global tea_count
    global red_tea_count
    
    if item == 'coffee':
        coffee_count += 1
        # frame1.text 
        return
    elif item == 'latte':
        latte_count += 1
        return
    elif item == 'smoothie':
        smoothie_count += 1
        return
    elif item == 'tea':
        tea_count += 1
        return
    elif item == 'red_tea':
        red_tea_count += 1
        return
    else:
        return


def btn_exit():
    msgbox = tk.messagebox.askquestion('확인', '주문을 마치겠습니까?')
    if msgbox == 'yes':
        
        exit()


window = tk.Tk()
window.title('음료 주문')
window.geometry('400x500+500+50')

frame1 = tk.Frame(window)
frame1.pack()


tk.Button(frame1, text='coffee',command=lambda: add('coffee'),width=20,height=2).grid(row=0, column=0)
tk.Button(frame1, text='latte',command=lambda: add('latte'),width=20,height=2).grid(row=1, column=0)
tk.Button(frame1, text='smoothie',command=lambda: add('smoothie'),width=20,height=2).grid(row=2, column=0)
tk.Button(frame1, text='tea',command=lambda: add('tea'),width=20,height=2).grid(row=3, column=0)
tk.Button(frame1, text='red tea',command=lambda: add('red tea'),width=20,height=2).grid(row=4, column=0)
tk.Button(frame1, text='coffee_cancel',command=lambda: cancel('coffee'),width=20,height=2).grid(row=0, column=1)
tk.Button(frame1, text='latte_cancel',command=lambda: cancel('latte'),width=20,height=2).grid(row=1, column=1)
tk.Button(frame1, text='smoothie_cancel',command=lambda: cancel('smoothie'),width=20,height=2).grid(row=2, column=1)
tk.Button(frame1, text='tea_cancel',command=lambda: cancel('tea'),width=20,height=2).grid(row=3, column=1)
tk.Button(frame1, text='red tea_cancel',command=lambda: cancel('red tea'),width=20,height=2).grid(row=4, column=1)
tk.Label(frame1, text=coffee_count,width=10,height=2).grid(row=0, column=2)
tk.Label(frame1, text=latte_count,width=10,height=2).grid(row=1, column=2)
tk.Label(frame1, text=smoothie_count,width=10,height=2).grid(row=2, column=2)
tk.Label(frame1, text=tea_count,width=10,height=2).grid(row=3, column=2)
tk.Label(frame1, text=red_tea_count,width=10,height=2).grid(row=4, column=2)
tk.Button(frame1, text='exit',command=btn_exit,width=20,height=2).grid(row=5, column=0)

label1 = tk.Label(window, text='금액: 0원',width=100, height=2,fg='blue')
label1.pack()

textarea = tk.Text(window)
textarea.pack()

window.mainloop()
