
import os
from tkinter import filedialog, font
from openpyxl import load_workbook
import openpyxl




# 파일 추가
def add_file():
    file = filedialog.askopenfilename(title="엑셀 데이타 파일을 선택하세요", \
        filetypes=(("EXCEL 파일", "*.xls"),('EXCEL 파일', '*.xlsm'), ("EXCEL 파일", "*.xlsx"), ("모든 파일", "*.*")))

    return file

    # if kind == 'welfare':
    #     txt_welfare_path.delete(0,END)
    #     txt_welfare_path.insert(0, files)
    #     return txt_welfare_path

    # elif kind == 'kind':
    #     txt_kind_welfare_path.delete(0,END)
    #     txt_kind_welfare_path.insert(0, files)
    #     return txt_kind_welfare_path

    # else:
    #     txt_template_path.delete(0,END)
    #     txt_template_path.insert(0, files)
    #     return txt_template_path

# 저장 경로 (폴더)
def browse_dest_path():
    folder_selected = filedialog.askdirectory()
    if folder_selected is None: # 사용자가 취소를 누를 때
        return
    # print(folder_selected)
    # txt_dest_path.delete(0, END)
    # txt_dest_path.insert(0, folder_selected)

path = add_file()
print(path)

# xls to xlsx
import win32com.client as win32
fname = path
excel = win32.gencache.EnsureDispatch('Excel.Application')
wb = excel.Workbooks.Open(fname)

wb.SaveAs(fname+"x", FileFormat = 51) #FileFormat = 51 is for .xlsx extension
wb.Close() #FileFormat = 56 is for .xls extension
excel.Application.Quit()


# import glob
# from win32com.client import Dispatch
# for file in glob.glob('*.xlsx'):
#     xl = Dispatch('Excel.Application')
#     wb = xl.Workbooks.Add(file)
#     wb.SaveAs(file[:-1], FileFormat=56)
#     xl.Quit()

wb_obj = load_workbook(path+'x')