from tkinter import Tk, Label, PhotoImage
   
if __name__ == "__main__":
    root = Tk()
    root.title("config 메소드를 이용한 방법")
     
    imgObj = PhotoImage(file = "image.gif")
      
    imgLabel = Label(root)
    imgLabel.config(image=imgObj)
    imgLabel.pack()
       
    root.mainloop()