import os
import pandas as pd
import tkinter.messagebox as msgbox
from tkinter import *
from tkinter import filedialog, font
from datetime import datetime

now = datetime.now()
yyyymm = now.strftime("%Y")+now.strftime("%m")+'월'
yyyy = now.strftime("%Y")

# 파일 추가
def add_file(kind):
    files = filedialog.askopenfilename(title="엑셀 데이타 파일을 선택하세요", \
        filetypes=(("EXCEL 파일", "*.xls"),('EXCEL 파일', '*.xlsm'), ("EXCEL 파일", "*.xlsx"), ("모든 파일", "*.*")))
    if kind == 'welfare':
        txt_welfare_path.delete(0,END)
        txt_welfare_path.insert(0, files)
        return txt_welfare_path

    elif kind == 'kind':
        txt_kind_welfare_path.delete(0,END)
        txt_kind_welfare_path.insert(0, files)
        return txt_kind_welfare_path

    else:
        txt_template_path.delete(0,END)
        txt_template_path.insert(0, files)
        return txt_template_path

# 저장 경로 (폴더)
def browse_dest_path():
    folder_selected = filedialog.askdirectory()
    if folder_selected is None: # 사용자가 취소를 누를 때
        return
    #print(folder_selected)
    txt_dest_path.delete(0, END)
    txt_dest_path.insert(0, folder_selected)

# 계산 시작
def start():
    # 각 옵션들 값을 확인
    f1 = txt_welfare_path.get()
    f2 = txt_kind_welfare_path.get()
    f3 = txt_template_path.get()
    f4 = txt_dest_path.get()

    # 파일 목록 확인
    if len(txt_welfare_path.get()) == 0:
        msgbox.showwarning("경고", "한전 복지감면 파일을 추가하세요")
        return

    if len(txt_kind_welfare_path.get()) == 0:
        msgbox.showwarning("경고", "한전 복지감면 종류 파일을 추가하세요")
        return

    if len(txt_template_path.get()) == 0:
        msgbox.showwarning("경고", "Template File을 추가하세요")
        return

    # 저장 경로 확인
    if len(txt_dest_path.get()) == 0:
        msgbox.showwarning("경고", "저장 경로를 선택하세요")
        return

    df2 = welfare_calc(f1)
    subset_df = kind_calc(f2)
    subset_df_w = subset_df[0]
    subset_df_f = subset_df[1]
    subset_df_a = subset_df[2]

    discount = discount_file(f3,df2,subset_df_w,subset_df_f,subset_df_a)
    pd_save(discount[0],f4)
    print('Total 사용량 보장공제액  :',discount[1])
    print('Total 대가족 할인 공제액 :',discount[2])
    print('Total 복지 할인 공제액   :',discount[3])
    
    return
    
def welfare_calc(f1):
    df = pd.read_excel(f1,skiprows=2)#, dtype={'동':int, '호':int}) #,thousands=',')
    new_col_names = ['동', '호', '동호명', '가구수', '계약종별', '요금적용전력', '사용량', '기본요금', '전력량요금',
       '기후환경요금', '연료비조정액', '필수사용공제', '복지추가 감액', '할인구분', '복지할인', '요금개편차액',
       '절전할인', '자동이체인터넷', '단수', '전기요금', '부가세', '전력기금', '전기바우처', '정산',
       '출산가구소급', '당월소계', 'TV수신료','청구금액']
    df.columns = new_col_names

    df1 = df.dropna(subset=['동','필수사용공제'])
    # Template Columns중에서 필수 Columns만 복사하여 DataFrame 생성용 Columns list 생성
    df2col =['동','호', '필수사용공제']
    # df2 DataFrame columns중에서 dtype float를 int로 바꿀 Columns list 생성
    df2col_f =['동','호', '필수사용공제']
    # SettingWithCopyWarning Error 방지를 위하여 copy() method적용
    df2 = df1[df2col].copy()
    df2[df2col_f] = df2[df2col_f].astype('int')
    return df2

def kind_calc(f2):
    df_w = pd.read_excel(f2,skiprows=2, thousands=',')#, dtype={'동':int, '호':int}) #,thousands=',')
    df_w = df_w[['동','호','복지구분','할인요금']]

    # 복지구분 컬럼을 선택합니다.
    # 컬럼의 값에 대가족할인 항목을 또는(|) 대가족할인 항목늬 문자열이 포함되어있는지 판단합니다.
    # 그 결과를 새로운 변수에 할당합니다.
    contains_family = df_w['복지구분'].str.contains('다자녀 할인|대가족 할인|출산가구 할인|의료기기 할인')
    contains_welfare = df_w['복지구분'].str.contains('장애인 할인|독립유공 할인|국가유공 할인|민주유공 할인|사회복지 할인|기초수급 할인|차상위계층 할인|기초수급 할인 (주거, 교육)')
    contains_addition = df_w['복지구분'].str.contains('추가복지감액')

    # 대가족할인 조건를 충족하는 데이터를 필터링하여 새로운 변수에 저장합니다.
    subset_df_f = df_w[contains_family].copy()
    subset_df_f.set_index(['동','호'],inplace=True)
    #subset_df_f['복지코드'] = subset_df_f['복지구분']
    subset_df_f.loc[subset_df_f.복지구분 == '다자녀 할인', '복지코드'] = '3'
    subset_df_f.loc[subset_df_f.복지구분 == '대가족 할인', '복지코드'] = '1'
    subset_df_f.loc[subset_df_f.복지구분 == '출산가구 할인', '복지코드'] = '2'
    subset_df_f.loc[subset_df_f.복지구분 == '의료기기 할인', '복지코드'] = '4'
    subset_df_f

    # 복지할인 조건를 충족(대가족할인이 아닌것 ~)하는 데이터를 필터링하여 새로운 변수에 저장합니다.
    subset_df_w = df_w[contains_welfare].copy()
    subset_df_w.set_index(['동','호'],inplace=True)
    subset_df_w.loc[subset_df_w.복지구분 == '장애인 할인', '복지코드'] = 'D'
    subset_df_w.loc[subset_df_w.복지구분 == '독립유공 할인', '복지코드'] = 'A'
    subset_df_w.loc[subset_df_w.복지구분 == '국가유공 할인', '복지코드'] = 'B'
    subset_df_w.loc[subset_df_w.복지구분 == '민주유공 할인', '복지코드'] = 'C'
    subset_df_w.loc[subset_df_w.복지구분 == '사회복지 할인', '복지코드'] = 'E'
    # subset_df_w.loc[subset_df_w.복지구분 == '복지추가감액', '복지코드'] = 'E'
    subset_df_w.loc[subset_df_w.복지구분 == '기초수급 할인', '복지코드'] = 'H'
    subset_df_w.loc[subset_df_w.복지구분 == '차상위계층 할인', '복지코드'] = 'I'
    subset_df_w.loc[subset_df_w.복지구분 == '기초수급 할인 (주거, 교육)', '복지코드'] = 'H'
    subset_df_w
    
    subset_df_add = df_w[contains_addition].copy()
    subset_df_add.set_index(['동','호'],inplace=True)
    subset_df_a = subset_df_add[['동','호','할인요금']]
    subset_df_a.rename(columns = {'할인요금' : '필수사용공제'}, inplace = True)

    return subset_df_f, subset_df_w, subset_df_a

def discount_file(f3,df2,subset_df_f,subset_df_w,subset_df_a):
    df_x = pd.read_excel(f3,skiprows=0)
    # xperp upload template 양식의 columns list 생성
    # df_x_cl = df_x.columns.tolist()
    # 동호를 indexing하여 dataFrame merge 준비
    df_x.set_index(['동','호'],inplace=True)
    # discount df 생성 (Template df(df_x)에 필수사용공제(df2) merge
    discount = pd.merge(df_x, df2, how = 'outer', on = ['동','호'])
    discount = pd.merge(discount, subset_df_a, how = 'outer', on = ['동','호'])   

    # 사용량 보장공제를 한전금액(필수사용공제) Data로 Update
    discount['사용량보장공제'] = discount['필수사용공제']
    # 사용량 보장공제 임시데이터 columns를 drop
    discount = discount.drop(['필수사용공제'],axis=1)
    # Template df에 필수사용공제 merge
    discount = pd.merge(discount, subset_df_f, how = 'outer', on = ['동','호'])
    discount['대가족할인액'] = discount['할인요금']
    discount['대가족할인구분'] = discount['복지코드']
    discount = discount.drop(['복지코드','할인요금','복지구분'],axis=1)
    discount = pd.merge(discount, subset_df_w, how = 'outer', on = ['동','호'])
    #discount1 = discount.reset_index()
    discount['복지할인액'] = discount['할인요금']
    discount['복지할인구분'] = discount['복지코드']
    discount = discount.drop(['복지코드','할인요금','복지구분'],axis=1)
    total_사용량보장공제 = discount['사용량보장공제'].sum()
    total_대가족할인액 = discount['대가족할인액'].sum()
    total_복지할인액 = discount['복지할인액'].sum()
    # display the result of computation
    txt_total_사용량.delete(0,END)
    txt_total_사용량.insert(0, f'{total_사용량보장공제:>20,}')

    txt_total_대가족.delete(0,END)
    txt_total_대가족.insert(0, f'{total_대가족할인액:>20,}')
    
    txt_total_복지.delete(0,END)
    txt_total_복지.insert(0, f'{total_복지할인액:>20,}')

    return discount, total_사용량보장공제, total_대가족할인액, total_복지할인액

def pd_save(discount,f4):

    #작업월을 파일이름에 넣기 위한 코드 (작업일 기준)
    now = datetime.now()
    dt1 = now.strftime("%Y")+now.strftime("%m")
    dt1 = dt1+'ELEC_XPERP_Upload_J_K_R_S_T_columns.xlsx'
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

root = Tk()
root.geometry('735x520+300+150')
root.title("전기감면 자료 작성 프로그램 Developed by LHT")

# Title Label
font1 = font.Font(family='맑은 고딕', size=15, weight='bold')
label = Label(root,
    text = '강남데시앙파크 아파트 관리사무소 전기감면 요금 관리 프로그램',
    font = font1, relief = 'solid', padx='10', pady='10')
label.pack()

# 복지 선택 프레임
welfare_frame = LabelFrame(root, text='한전 복지 할인 및 필수사용공제 감면자료 파일선택')
welfare_frame.pack(fill="x", padx=5, pady=5, ipady=5)

txt_welfare_path = Entry(welfare_frame)
txt_welfare_path.insert(0,'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/전기감면자료')
txt_welfare_path.pack(side="left", fill="x", expand=True, padx=5, pady=5, ipady=4) 

btn_welfare_path = Button(welfare_frame, text="복지할인", width=10, command=lambda:add_file('welfare'))
btn_welfare_path.pack(side="right", padx=5, pady=5)

# 복지종류 선택 프레임
kind_welfare_frame = LabelFrame(root,text='한전 복지 할인 종류 및 감면요금 자료 파일선택')
kind_welfare_frame.pack(fill="x", padx=5, pady=5, ipady=5)

txt_kind_welfare_path = Entry(kind_welfare_frame)
txt_kind_welfare_path.insert(0,'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/전기감면자료')
txt_kind_welfare_path.pack(side="left", fill="x", expand=True, padx=5, pady=5, ipady=4) 

btn_kind_welfare_path = Button(kind_welfare_frame, text="할인종류", width=10, command=lambda:add_file('kind'))
btn_kind_welfare_path.pack(side="right", padx=5, pady=5)

# Template File SElection Frame
template_frame = LabelFrame(root,text='XPERP Upload용 Template 파일선택')
template_frame.pack(fill="x", padx=5, pady=5, ipady=5)

txt_template_path = Entry(template_frame)
txt_template_path.insert(0,'D:/과장/1 1 부과자료/'+yyyy+'년/Templates/Elec_Template_File_for_XPERP_upload.xls')
txt_template_path.pack(side="left", fill="x", expand=True, padx=5, pady=5, ipady=4) 

btn_template_path = Button(template_frame, text="Template", width=10, command=lambda:add_file('template'))
btn_template_path.pack(side="right", padx=5, pady=5)

# 저장 경로 프레임
path_frame = LabelFrame(root, text="XPERP 할인자료 업로드파일 저장경로")
path_frame.pack(fill="x", padx=5, pady=5, ipady=5)

txt_dest_path = Entry(path_frame)
txt_dest_path.insert(0, 'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/xperp_감면자료')
txt_dest_path.pack(side="left", fill="x", expand=True, padx=5, pady=5, ipady=4)

btn_dest_path = Button(path_frame, text="저장경로", width=10, command=browse_dest_path)
btn_dest_path.pack(side="right", padx=5, pady=5)

# 계산결과 합계액 프레임
total_frame = LabelFrame(root, text="공제 종류별 총 공제요금 합계액 현황표")
total_frame.pack(fill="x", padx=5, pady=5, ipady=5)

lbl_total_사용량 = Label(total_frame, text="사용량보장")
lbl_total_사용량.pack(side="left", fill="x", expand=False, padx=5, pady=5, ipady=4) 

txt_total_사용량 = Entry(total_frame, font = ('', 11, 'bold'))
txt_total_사용량.pack(side="left", fill="x", expand=False, padx=5, pady=5, ipady=4) 

lbl_total_대가족 = Label(total_frame, text="대가족")
lbl_total_대가족.pack(side="left", fill="x", expand=False, padx=5, pady=1, ipady=4) 

txt_total_대가족 = Entry(total_frame, font = ('', 11, 'bold'))
txt_total_대가족.pack(side="left", fill="x", expand=False, padx=5, pady=1, ipady=4) 

lbl_total_복지 = Label(total_frame, text="복지할인")
lbl_total_복지.pack(side="left", fill="x", expand=False, padx=5, pady=1, ipady=4)

txt_total_복지 = Entry(total_frame, font = ('', 11, 'bold'))
txt_total_복지.pack(side="left", fill="x", expand=False, padx=5, pady=1, ipady=4)

# 실행 프레임
frame_run = Frame(root)
frame_run.pack(fill="x", padx=5, pady=5)

label_originator = Label(frame_run, padx=5, pady=5, text="프로그램 작성 : 임훈택 Rev 2, 2021.12.27 Revised")
label_originator.pack(side="left", padx=5, pady=5)

btn_close = Button(frame_run, padx=5, pady=5, text="종료", width=12, command=root.quit)
btn_close.pack(side="right", padx=5, pady=5)

btn_start = Button(frame_run, padx=5, pady=5, text="계산시작", width=12, command=start)
btn_start.pack(side="right", padx=5, pady=5)

root.resizable(True, True)
root.mainloop()
