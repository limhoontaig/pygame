import sys
import os
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal
from PyQt5 import uic
from datetime import datetime

def resource_path(relative_path):
    base_path = getattr(sys, "_MAIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form = resource_path("수도감면_mainwindow.ui")
form_class = uic.loadUiType(form)[0]

now = datetime.now()
yyyymm = now.strftime("%Y")+now.strftime("%m")+'월'
yyyy = now.strftime("%Y")

LE =  [
    'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/수도감면자료',
    'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/수도감면자료',
    'D:/과장/1 1 부과자료/'+yyyy+'년/Water_Template_File_for_XPERP_upload.xls',
    'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/xperp_감면자료'
    ]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.LE = LE
        self.setupUi(self)

        self.tableWidget.setRowCount(28)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setHorizontalHeaderLabels(['No', '고객번호', '동호수'])
        self.tableWidget.setSortingEnabled(True) # default ; False

        self.lineEdit.setText(LE[0])
        self.lineEdit_2.setText(LE[1])
        self.lineEdit_3.setText(LE[2])
        self.lineEdit_4.setText(LE[3])
        self.label_5.setText('프로그램 작성 : 임훈택 Rev 0, 2022.05.11 Issued')

        self.pushButton.clicked.connect(self.add_file)
        self.pushButton_2.clicked.connect(self.add_file)
        self.pushButton_3.clicked.connect(self.add_file)
        self.pushButton_4.clicked.connect(self.add_file)
        self.pushButton_5.clicked.connect(self.start)
        #self.pushButton_7.clicked.connect(self.기초생활)
        #self.pushButton_8.clicked.connect(self.중증장애)
        self.pushButton_9.clicked.connect(self.tableWidget.scrollToTop)
        self.pushButton_10.clicked.connect(self.tableWidget.scrollToBottom)
        #self.pushButton_11.clicked.connect(self.다자녀)
        #self.pushButton_12.clicked.connect(self.유공자)

        self.pushButton_6.clicked.connect(self.close)

    def set_tbl(self, df):

        rdr_col = len(df.columns)
        rdr_row = (df.index)
        
        self.tableWidget.clear()
        self.tableWidget.setHorizontalHeaderLabels(['No', '고객번호', '동호수'])
        self.tableWidget.setRowCount(rdr_row)
        self.tableWidget.setColumnCount(rdr_col)
        for i in range(rdr_row):
            for j in range(rdr_col):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(df.iget_value(i,j))))
        #app.exec_()

    @pyqtSlot()
    def add_file(self):

        sname = self.sender().text()

        if sname == '복지/가족':
            init_dir = self.LE[0]
            fname = QFileDialog.getOpenFileName(self, '엑셀 데이타 파일을 선택하세요', init_dir, 'All Files (*) :: Excel (*.xls *.xlsx)')
            if len(fname[0]) != 0:
                self.lineEdit.setText(fname[0])
            else:
                self.lineEdit.setText(LE[0])

        elif sname == '중증/유공':
            init_dir = self.LE[1]
            fname = QFileDialog.getOpenFileName(self, '엑셀 데이타 파일을 선택하세요', init_dir, 'All Files (*) :: Excel (*.xls *.xlsx)')
            if len(fname[0]) != 0:
                self.lineEdit_2.setText(fname[0])
            else:
                self.lineEdit_2.setText(LE[1])
        
        elif sname == 'Template':
            init_dir = self.LE[2]
            fname = QFileDialog.getOpenFileName(self, '엑셀 데이타 파일을 선택하세요', init_dir, 'All Files (*) :: Excel (*.xls *.xlsx)')
            if len(fname[0]) != 0:
                self.lineEdit_3.setText(fname[0]) 
            else: 
                self.lineEdit_3.setText(LE[2])
        
        else:
            init_dir = self.LE[3]
            fname = QFileDialog.getExistingDirectory(self, '저장 Direttory를 선택하새요', init_dir)
            if len(fname) != 0:
                self.lineEdit_4.setText(fname)
            else:
                self.lineEdit_4.setText(LE[3])

    # 계산 시작
    def start(self):
        # 각 옵션들 값을 확인
        f1 = self.lineEdit.text()
        f2 = self.lineEdit_2.text()
        f3 = self.lineEdit_3.text()
        f4 = self.lineEdit_4.text()

        # 파일 목록 확인
        if '.xls' not in f1 or f1 == 0:
            QMessageBox.about(self, "경고", "수도 기초수급/다자녀 감면 파일을 추가하세요")
            return
        
        if '.xls' not in f2 or f2 == 0:
            QMessageBox.about(self, "경고", "수도 중증장애인/유공자 감면 파일을 추가하세요")
            return

        if '.xls' not in f3 or f3 == 0:
            QMessageBox.about(self, "경고", "Template File을 추가하세요")
            return

        # 저장 경로 확인
        if f4 == 0:
            QMessageBox.about(self, "경고", "저장 경로를 선택하세요")
            return

        df2 = self.welfare_calc(f1)
        df = df2[0]
        df.rename(columns = {'복지코드' : '기초'}, inplace = True)
        df_f = df2[1]
        df_f.rename(columns = {'복지코드' : '가족'}, inplace = True)

        df_temp = self.merits_calc(f2)
        df3 = df_temp[0]
        df3.rename(columns = {'복지코드' : '중증'}, inplace = True)
        df4 = df_temp[1]
        df4.rename(columns = {'복지코드' : '유공'}, inplace = True)
        print('df', df)
        print('df_f', df_f)
        print('df3', df3)
        print('df4', df4)
        discount = self.template_make(f3,df,df_f,df3,df4)
        
        self.pd_save(discount,f4)
        return

    def welfare_calc(self, f1):
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
        # txt_total_복지.delete(0,END)
        # txt_total_복지.insert(0, f'{total_복지:>7,}')
        
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
        #txt_total_대가족.delete(0,END)
        #txt_total_대가족.insert(0, f'{total_대가족:>7,}')
        
        return df, df_f

    def merits_calc(self, f2):
        # # 수도 유공자할인 등록
        f = pd.ExcelFile(f2)
        parse_file = self.seperate_dongho(f)

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
        #txt_total_유공자.delete(0,END)
        #txt_total_유공자.insert(0, f'{total_유공자:>7,}')

        return df_3, df_4

    def seperate_dongho(self, f):
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


    def template_make(self, f3,df,df_f,df_3,df_4):
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

    def pd_save(self, discount,f4):

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()