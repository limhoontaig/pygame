import os
import pandas as pd
import tkinter.messagebox as msgbox
from tkinter import * # __all__
from tkinter import filedialog, ttk, font
from datetime import datetime

now = datetime.now()
yyyy = now.strftime("%Y")+'년'
yyyymm = now.strftime("%Y")+now.strftime("%m")+'월'

root = Tk()
root.geometry('750x490+300+150')
root.title("수도감면 자료 작성 프로그램 Produced by LHT")

# 파일 추가
def add_file(initialDir, kind):
    files = filedialog.askopenfilename(initialdir = initialDir, title="엑셀 데이타 파일을 선택하세요", \
        filetypes=(("EXCEL 파일", "*.xls"),('EXCEL 파일', '*.xlsm'), ("EXCEL 파일", "*.xlsx"), ("모든 파일", "*.*")))
    
    if kind == 'welfare':
        txt_welfare_path.delete(0,END)
        txt_welfare_path.insert(0, files)
        return txt_welfare_path

    elif kind == 'template':
        txt_template_path.delete(0,END)
        txt_template_path.insert(0, files)
        return txt_template_path

    else:
        txt_merits_path.delete(0,END)
        txt_merits_path.insert(0, files)
        return txt_merits_path

# 저장 경로 (폴더)
def browse_dest_path():
    folder_selected = filedialog.askdirectory()
    if folder_selected is None: # 사용자가 취소를 누를 때
        return
    # display on window of folder_selected
    txt_dest_path.delete(0, END)
    txt_dest_path.insert(0, folder_selected)

# 시작
def start():
    # 각 옵션들 값을 읽어와 변수에 저장
    f1 = txt_welfare_path.get()
    f2 = txt_merits_path.get()
    f3 = txt_template_path.get()
    f4 = txt_dest_path.get()
    # print(f1,f2,f3,f4)

    # 파일 목록 확인
    if len(txt_welfare_path.get()) == 0:
        msgbox.showwarning("경고", "수도 기초수급/다자녀 감면 파일을 추가하세요")
        return

    if len(txt_merits_path.get()) == 0:
        msgbox.showwarning("경고", "수도 중증장애인/유공자 감면 파일을 추가하세요")
        return

    if len(txt_template_path.get()) == 0:
        msgbox.showwarning("경고", "Template File을 추가하세요")
        return

    # 저장 경로 확인
    if len(txt_dest_path.get()) == 0:
        msgbox.showwarning("경고", "저장 경로를 선택하세요")
        return

    df2 = welfare_calc(f1)
    df = df2[0]
    df.rename(columns = {'복지코드' : '기초'}, inplace = True)
    df_f = df2[1]
    df_f.rename(columns = {'복지코드' : '가족'}, inplace = True)

    df_temp = merits_calc(f2)
    df3 = df_temp[0]
    df3.rename(columns = {'복지코드' : '중증'}, inplace = True)
    df4 = df_temp[1]
    df4.rename(columns = {'복지코드' : '유공'}, inplace = True)
    print('df', df)
    print('df_f', df_f)
    print('df3', df3)
    print('df4', df4)
    discount = template_make(f3,df,df_f,df3,df4)
    
    pd_save(discount,f4)
    return
        
def welfare_calc(f1):
    df = pd.read_excel(f1,sheet_name=0, skiprows=0)

    #df['동'] = df['동호수(복지개별)'].parse('-', 0)
    # new list of data frame with split value columns
    new = df['동호수(복지개별)'].str.split("-", n = 1, expand = True)
    
    # making separate first name column from new data frame
    df["동"]= new[0]
    
    # making separate last name column from new data frame
    df["호"]= new[1]
    
    # Dropping old Name columns
    df.drop(columns =["No","동호수(복지개별)"], inplace = True)

    # making 복지코드 on '복지코드' column from XPERP Code
    df["복지코드"]= '3'

    # display the data of welfare homes
    total_복지 = len(df)
    txt_total_복지.delete(0,END)
    txt_total_복지.insert(0, f'{total_복지:>7,}')
    
    # XPERP Code 유공자: 2, 기초생활:3, 다자녀:I(Capital i), 중복할인: V(Capital v)  ###

    # 다자녀 시트 읽어오기
    df_f = pd.read_excel(f1, sheet_name=1,skiprows=0)

    # new data frame with split value columns
    new = df_f['동호수(다자녀감면)'].str.split("-", n = 1, expand = True)
    
    # making separate 동 name column from new data frame
    df_f["동"]= new[0]
    
    # making separate 호 name column from new data frame
    df_f["호"]= new[1]

    # making 복지코드 on '복지코드' column from XPERP Code
    df_f["복지코드"]= 'I' # Capital I
    
    # Dropping old Name columns
    df_f.drop(columns =["No","동호수(다자녀감면)"], inplace = True)
    
    # display the data of large homes
    total_대가족 = len(df_f)
    txt_total_대가족.delete(0,END)
    txt_total_대가족.insert(0, f'{total_대가족:>7,}')
    
    return df, df_f

def merits_calc(f2):
    # # 수도 유공자할인 등록
    f = pd.ExcelFile(f2)
    parse_file = seperate_dongho(f)

    '''sheet_name = f.sheet_names 
    df__ = pd.read_excel(f2, sheet_name=sheet_name[0])
    cols = df__.columns
    if cols[0] == 'No':
        rows = -1
    else:
        s = df__.index[(df__["Unnamed: 0"] == "No")].tolist()
        rows = s[0]
    
    df_ = pd.read_excel(f2, sheet_name=0, skiprows=rows+1)
    df_3 = df_[['No','동호수']].copy()
    # new data frame with split value columns
    temp = df_3['동호수'].str.split(" 동", n = 1, expand = True)
    df_3["동"] = temp[0]
    temp_1 = temp[1].str.slice(stop=-1)
    df_3['호'] = temp_1
    print(df_3)
    # making separate first name column from new data frame
    #   df_3["동"]= new[0]
    # making separate last name column from new data frame
    #    df_3["호"]= new[1]
    # Dropping old Name columns
    df_3.drop(columns =["No","동호수"], inplace = True)'''
    # making 복지코드 on '복지코드' column from XPERP Code
    df_3 = parse_file[0]
    df_3["복지코드"]= 'T' #
    print(df_3) 
    df_4 = parse_file[1]
    df_4["복지코드"]= '2'
    print(df_4) 


    # display the data of 유공자
    total_유공자 = len(df_3)
    txt_total_유공자.delete(0,END)
    txt_total_유공자.insert(0, f'{total_유공자:>7,}')

    return df_3, df_4

def seperate_dongho(f):
    sheet_name = f.sheet_names
    sheets = []
    for sheet in sheet_name:
        df__ = pd.read_excel(f,sheet_name = sheet)
        cols = df__.columns
        if cols[0] == 'No':
            rows = -1
        else:
            s = df__.index[(df__["Unnamed: 0"] == "No")].tolist()
            rows = s[0]
        sheet = pd.ExcelFile.parse(f, sheet_name=sheet,skiprows=rows+1)
        temp = sheet['동호수'].str.split('동 ', expand = True)
        sheet['동'] = temp[0]
        temp_1 = temp[1].str.slice(stop = -1)
        sheet['호'] = temp_1
        df_1 = sheet[['동', '호']]
        
        sheets.append(df_1)

    return sheets


def template_make(f3,df,df_f,df_3,df_4):
    dis = pd.merge(df, df_f, how = 'outer', on = ['동','호'])
    print('dis', dis)
    dis1 = pd.merge(dis, df_3, how = 'outer', on = ['동','호'])
    print('dis1', dis1)
    dis2 = pd.merge(dis1, df_4, how = 'outer', on = ['동','호'])
    print('dis2', dis2)
    #discount_1.fillna(0)
    dis_code = {''}
    con1 = (dis2.기초=='3') # 기초생활
    con2 = (dis2.가족=='I') # 다자녀
    con3 = (dis2.중증=='T') # 중증장애인
    con4 = (dis2.유공=='2') # 유공자
    dis2.loc[con1, 'Code'] = '3'
    dis2.loc[con2, 'Code'] = 'I'
    dis2.loc[con3, 'Code'] = 'T'
    dis2.loc[con4, 'Code'] = '2'

    dis2.loc[(con1&con2)|(con1&con3)|(con2&con3)|(con1&con2&con3), 'Code'] = 'V' # 중복할인
    dis3 = dis2[['동','호','Code']]

    # dis2['동'] = pd.to_numeric(dis2['동'])
    # dis2['호'] = pd.to_numeric(dis2['호'])
    dis3 = dis3.astype({'동':int, '호':int})

    # 복지종류별 입력하기
    # Template dataframe 작성

    df_x = pd.read_excel(f3,skiprows=0)

    # discount df 생성 (Template df(df_x)에 감면코드(discount) merge
    discount = pd.merge(df_x, dis3, how = 'outer', on = ['동','호'])
    # 감면구분 코드를 Code Data로 Update
    discount['감면구분'] = discount['Code']
    # Code 임시데이터 columns를 drop
    discount = discount.drop(['Code'],axis=1)
    return discount

def pd_save(discount,f4):

    #작업월을 파일이름에 넣기 위한 코드 (작업일 기준)
    now = datetime.now()
    dt1 = now.strftime("%Y")+now.strftime("%m")
    dt1 = dt1+'WATER_XPERP_Upload_i_columns.xlsx'
    file_name = f4+'/'+dt1

    #file save
    if os.path.isfile(file_name):
        os.remove(file_name)
        discount.to_excel(file_name,index=False,header=False)
    else:
        discount.to_excel(file_name,index=False,header=False)
    
    dttemp = file_name.split('.')
    dt2 = dttemp[0] + '.xls'

    if os.path.isfile(dt2):
        os.remove(dt2)
        os.rename(file_name, dt2)   
    else:
        os.rename(file_name, dt2)
    
    return

# Title Label
font = font.Font(family='맑은 고딕', size=15, weight='bold')

label = Label(root,
    text = '강남데시앙파크 아파트 관리사무소 수도감면 요금 관리 프로그램',
    font = font, relief = 'solid', padx='10', pady='10')
label.pack()

# 복지 선택 프레임
welfare_frame = LabelFrame(root, text='수도 복지 할인(다자녀,기초생활) 감면자료 파일선택')
welfare_frame.pack(fill="x", padx=5, pady=5, ipady=5)

txt_welfare_path = Entry(welfare_frame)
txt_welfare_path.insert(0, 'D:/과장/1 1 부과자료/'+yyyy+'/'+yyyymm+'/수도감면자료')
txt_welfare_path.pack(side="left", fill="x", expand=True, padx=5, pady=5, ipady=4) # 높이 변경

btn_welfare_path = Button(welfare_frame, text="수도할인", width=10, command=lambda:add_file(txt_welfare_path, 'welfare'))
btn_welfare_path.pack(side="right", padx=5, pady=5)

# 유공할인 선택 프레임
kind_merits_frame = LabelFrame(root,text='수도 중증장애인/유공자 할인 감면자료 파일선택')
kind_merits_frame.pack(fill="x", padx=5, pady=5, ipady=5)

txt_merits_path = Entry(kind_merits_frame)
txt_merits_path.insert(0, 'D:/과장/1 1 부과자료/'+yyyy+'/'+yyyymm+'/수도감면자료')
txt_merits_path.pack(side="left", fill="x", expand=True, padx=5, pady=5, ipady=4) # 높이 변경

btn_merits_path = Button(kind_merits_frame, text="유공할인", width=10, command=lambda:add_file(txt_merits_path, 'merits'))
btn_merits_path.pack(side="right", padx=5, pady=5)

# Template File SElection Frame
template_frame = LabelFrame(root,text='XPERP Upload용 Template 파일선택')
template_frame.pack(fill="x", padx=5, pady=5, ipady=5)

txt_template_path = Entry(template_frame)
txt_template_path.insert(0,'D:/과장/1 1 부과자료/'+yyyy+'/Templates/Water_Template_File_for_XPERP_upload.xls')
txt_template_path.pack(side="left", fill="x", expand=True, padx=5, pady=5, ipady=4) # 높이 변경

btn_template_path = Button(template_frame, text="Template", width=10, command=lambda:add_file(txt_template_path, 'template'))
btn_template_path.pack(side="right", padx=5, pady=5)

# 저장 경로 프레임
path_frame = LabelFrame(root, text="XPERP 할인자료 업로드파일 저장경로")
path_frame.pack(fill="x", padx=5, pady=5, ipady=5)

txt_dest_path = Entry(path_frame)
txt_dest_path.insert(0, 'D:/과장/1 1 부과자료/'+yyyy+'/'+yyyymm+'/xperp_감면자료')
txt_dest_path.pack(side="left", fill="x", expand=True, padx=5, pady=5, ipady=4) # 높이 변경

btn_dest_path = Button(path_frame, text="저장경로", width=10, command=browse_dest_path)
btn_dest_path.pack(side="right", padx=5, pady=5)

# 계산결과 공제세대 합계 프레임
total_frame = LabelFrame(root, text="공제 종류별 총 공제세대 현황표")
total_frame.pack(fill="x", padx=5, pady=5, ipady=5)

lbl_total_복지 = Label(total_frame, text="복지할인 세대")
lbl_total_복지.pack(side="left", fill="x", expand=False, padx=1, pady=5, ipady=4) 

txt_total_복지 = Entry(total_frame, font = ('', 10, 'bold'))
txt_total_복지.pack(side="left", fill="x", expand=False, padx=1, pady=5, ipady=4) 

lbl_total_대가족 = Label(total_frame, text="대가족할인 세대")
lbl_total_대가족.pack(side="left", fill="x", expand=False, padx=1, pady=1, ipady=4) 

txt_total_대가족 = Entry(total_frame, font = ('', 10, 'bold'))
txt_total_대가족.pack(side="left", fill="x", expand=False, padx=1, pady=1, ipady=4) 

lbl_total_유공자 = Label(total_frame, text="유공자할인 세대")
lbl_total_유공자.pack(side="left", fill="x", expand=False, padx=1, pady=1, ipady=4)

txt_total_유공자 = Entry(total_frame, font = ('', 10, 'bold'))
txt_total_유공자.pack(side="left", fill="x", expand=False, padx=1, pady=1, ipady=4)

# 실행 프레임
frame_run = Frame(root)
frame_run.pack(fill="x", padx=5, pady=5)

label_originator = Label(frame_run, padx=5, pady=5, text="프로그램 작성 : 임훈택 Rev 3, 2021.11.16 Modified")
label_originator.pack(side="left", padx=5, pady=5)

btn_close = Button(frame_run, padx=5, pady=5, text="닫기", width=12, command=root.quit)
btn_close.pack(side="right", padx=5, pady=5)

btn_start = Button(frame_run, padx=5, pady=5, text="시작", width=12, command=start)
btn_start.pack(side="right", padx=5, pady=5)

root.resizable(True, True)
root.mainloop()

# if __name__ == '__main__':
#     root.mainloop()
