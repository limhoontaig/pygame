import tkinter.ttk as ttk
import tkinter.messagebox as msgbox
from tkinter import * # __all__
from tkinter import filedialog

root = Tk()
root.geometry('600x300+300+150')
root.title("전기감면 자료 작성 프로그램 Produced by LHT")

# 파일 추가
def add_file(kind):
    files = filedialog.askopenfilename(title="엑셀 데이타 파일을 선택하세요", \
        filetypes=(("EXCEL 파일", "*.xls"), ("EXCEL 파일", "*.xlsx"), ("모든 파일", "*.*")), \
        initialdir=r"C:\Users\Nadocoding\Desktop\PythonWorkspace\pygame_project\images")
    if kind == 'welfare':
        txt_welfare_path.delete(0,END)
        txt_welfare_path.insert(0, files)
        return txt_welfare_path
    else:
        txt_kind_welfare_path.delete(0,END)
        txt_kind_welfare_path.insert(0, files)
        return txt_kind_welfare_path
        # 최초에 사용자가 지정한 경로를 보여줌

# 저장 경로 (폴더)
def browse_dest_path():
    folder_selected = filedialog.askdirectory()
    if folder_selected is None: # 사용자가 취소를 누를 때
        return
    #print(folder_selected)
    txt_dest_path.delete(0, END)
    txt_dest_path.insert(0, folder_selected)

# 시작
def start():
    # 각 옵션들 값을 확인
    print("복지감면 파일 : ", txt_welfare_path.get())
    print("감면종류 파일 : ", txt_kind_welfare_path.get())
    print("저장 디렉토리 : ", txt_dest_path.get())
    f1 = txt_welfare_path.get()
    f2 = txt_kind_welfare_path.get()
    f3 = txt_dest_path.get()
    

    # 파일 목록 확인
    if len(txt_welfare_path.get()) == 0:
        msgbox.showwarning("경고", "한전 복지감면 파일을 추가하세요")
        return

    if len(txt_kind_welfare_path.get()) == 0:
        msgbox.showwarning("경고", "한전 복지감면 종류 파일을 추가하세요")
        return


    # 저장 경로 확인
    if len(txt_dest_path.get()) == 0:
        msgbox.showwarning("경고", "저장 경로를 선택하세요")
        return

# text_welfare_path = StringVar(Value = '')
# text_kind_welfare_path = StringVar(Value = '')
# text_dest_path = StringVar(Value = '')

# 복지 선택 프레임
welfare_frame = LabelFrame(root,text='한전 복지 할인 및 필수사용공제 감면자료 파일선택')
welfare_frame.pack(fill="x", padx=5, pady=5, ipady=5)

txt_welfare_path = Entry(welfare_frame)
txt_welfare_path.pack(side="left", fill="x", expand=True, padx=5, pady=5, ipady=4) # 높이 변경

btn_welfare_path = Button(welfare_frame, text="복지할인", width=10, command=lambda:add_file('welfare'))
btn_welfare_path.pack(side="right", padx=5, pady=5)

# 복지종류 선택 프레임
kind_welfare_frame = LabelFrame(root,text='한전 복지 할인 종류 및 감면요금 자료 파일선택')
kind_welfare_frame.pack(fill="x", padx=5, pady=5, ipady=5)

txt_kind_welfare_path = Entry(kind_welfare_frame)
txt_kind_welfare_path.pack(side="left", fill="x", expand=True, padx=5, pady=5, ipady=4) # 높이 변경

btn_kind_welfare_path = Button(kind_welfare_frame, text="할인종류", width=10, command=lambda:add_file('kind'))
btn_kind_welfare_path.pack(side="right", padx=5, pady=5)

# 저장 경로 프레임
path_frame = LabelFrame(root, text="XPERP 할인자료 업로드파일 저장경로")
path_frame.pack(fill="x", padx=5, pady=5, ipady=5)

txt_dest_path = Entry(path_frame)
txt_dest_path.pack(side="left", fill="x", expand=True, padx=5, pady=5, ipady=4) # 높이 변경

btn_dest_path = Button(path_frame, text="찾아보기", width=10, command=browse_dest_path)
btn_dest_path.pack(side="right", padx=5, pady=5)

# # 파일 포맷 옵션 콤보
# opt_format = ["PNG", "JPG", "BMP"]
# cmb_format = ttk.Combobox(frame_option, state="readonly", values=opt_format, width=10)
# cmb_format.current(0)
# cmb_format.pack(side="left", padx=5, pady=5)

# 실행 프레임
frame_run = Frame(root)
frame_run.pack(fill="x", padx=5, pady=5)

btn_close = Button(frame_run, padx=5, pady=5, text="닫기", width=12, command=root.quit)
btn_close.pack(side="right", padx=5, pady=5)

btn_start = Button(frame_run, padx=5, pady=5, text="시작", width=12, command=start)
btn_start.pack(side="right", padx=5, pady=5)

root.resizable(True, True)
root.mainloop()