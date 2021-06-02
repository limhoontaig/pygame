from tkinter import *

root = Tk()
root.title('LHT GUI')
root.geometry('600x480+300+100')

root.resizable(False, False) 

label1 = Label(root,text='Good Morning!')
label1.pack()

photo = PhotoImage('gui_project/img.png')
label2 = Label(root,image=photo)
label2.pack()

photo2 = PhotoImage('gui_project/img2.png')
label3 = Label(root,image=photo2)
label3.pack()

def change():
    label1.config(text='See you again!')


btn1 = Button(root, text='Button change', command=change)
btn1.pack()

btn2 = Button(root, padx=10, pady=10, text ='Button / save the file or not?')
btn2.pack()

btn3 = Button(root, padx=100, pady=10, text ='Button 3')
btn3.pack()

btn4 = Button(root, width=10, height=3, text ='Button / save the children')
btn4.pack()

btn5 = Button(root, padx=5, pady=3, fg='red', bg='yellow', text ='Button 5')

# photo = PhotoImage(file='gui_project/img.png')
# btn6 = Button(root, image=photo,padx=5, pady=30)
# btn6.pack()

def btncmd7():
    print('버튼이 동작하였어요.')

btn7 = Button(root, text='동작하는 버튼', command = btncmd7, padx=5, pady=30)
btn7.pack()


root.mainloop()
