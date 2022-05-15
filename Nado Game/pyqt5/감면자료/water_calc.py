import collections
from email import header
import sys
import os
import openpyxl
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal
from PyQt5 import uic
from datetime import datetime

def resource_path(relative_path):
    base_path = getattr(sys, "_MAIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form = resource_path("water_mainwindow.ui")
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
        self.tableWidget.setHorizontalHeaderLabels(['No', '사용가번호', '동호수'])
        #self.tableWidget.resizeColumnToContents()
        #self.tableWidget.resizeRowToContents()
        self.tableWidget.setEditTriggers(QAbstractItemView.AllEditTriggers) # QAbstractItemView.NoEditTriggers
        self.tableWidget.cellChanged.connect(self.cellchanged_event)
        

        self.tableWidget.setSortingEnabled(False) # default ; False

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
        self.pushButton_7.clicked.connect(self.data_verify)
        self.pushButton_8.clicked.connect(self.data_verify)
        self.pushButton_9.clicked.connect(self.tableWidget.scrollToTop)
        self.pushButton_10.clicked.connect(self.tableWidget.scrollToBottom)
        self.pushButton_11.clicked.connect(self.data_verify)
        self.pushButton_12.clicked.connect(self.data_verify)
        self.pushButton_16.clicked.connect(self.data_change_save)
        self.pushButton_13.clicked.connect(self.data_change_save)
        self.pushButton_15.clicked.connect(self.data_change_save)
        self.pushButton_14.clicked.connect(self.data_change_save)
        self.pushButton_16.setDisabled(True)
        self.pushButton_13.setDisabled(True)
        self.pushButton_15.setDisabled(True)
        self.pushButton_14.setDisabled(True)

        self.pushButton_6.clicked.connect(self.close)

    def data_query(self):
        '''
        data query from tablewidget to pandas dataframe
        '''
        rowcount = self.tableWidget.rowCount()
        colcount = self.tableWidget.columnCount()
        
        headers = [self.tableWidget.horizontalHeaderItem(x).text() for x in range(0,colcount)]
        data_list = []
        for i in range(0, rowcount):
            data =[]
            for j in range(0, colcount):
                d = self.tableWidget.item(i,j).text()
                data.append(d)
            data_list.append(data)
        df = pd.DataFrame(data_list) # list to dataframe
        df.columns = headers # set the hwaders on dataframe
        
        return df

    def data_change_save(self):
        sname = self.sender().text()
        if sname == '복지저장': # 코드 : 복지
            file = self.lineEdit.text()

        elif sname == '다자녀저장':
            file = self.lineEdit.text()
            
        elif sname == '중증장애저장':
            file = self.lineEdit_2.text()
        else:
            sname = '유공자저장'
            file = self.lineEdit_2.text()

        code = sname[:2]
        with pd.ExcelFile(file) as f:
            sheet = self.sheet_select(f,code)
        df = self.data_query()
        f_split = file.split('.')
        file = f_split[0]+sheet+'.'+f_split[1]

        if os.path.isfile(file):
            os.remove(file)
            df.to_excel(file,sheet_name= sheet,index=False,header=True)
        else:
            df.to_excel(file,sheet_name= sheet,index=False,header=True)

        if sname == '복지저장': # 코드 : 복지
            self.lineEdit_9.setText(file)

        elif sname == '다자녀저장':
            self.lineEdit_12.setText(file)
            
        elif sname == '중증장애저장':
            self.lineEdit_13.setText(file)
        else:
            sname = '유공자저장'
            self.lineEdit_14.setText(file)
        
        return

    def cellchanged_event(self, row, col):
        data = self.tableWidget.item(row,col)

    def data_verify(self):
        sname = self.sender().text()
        if sname == '복지': # 코드 : 복지
            file = self.lineEdit.text()
            if '.xls' not in file or file == 0:
                QMessageBox.about(self, "경고", "수도 다자녀/복지감면 파일을 추가하세요")
                return
            self.pushButton_16.setDisabled(False)
            self.pushButton_13.setDisabled(True)
            self.pushButton_15.setDisabled(True)
            self.pushButton_14.setDisabled(True)

        elif sname == '다자녀':
            file = self.lineEdit.text()
            if '.xls' not in file or file == 0:
                QMessageBox.about(self, "경고", "수도 다자녀/복지감면 파일을 추가하세요")
                return
            self.pushButton_16.setDisabled(True)
            self.pushButton_13.setDisabled(False)
            self.pushButton_15.setDisabled(True)
            self.pushButton_14.setDisabled(True)
        elif sname == '중증장애':
            file = self.lineEdit_2.text()
            if '.xls' not in file or file == 0:
                QMessageBox.about(self, "경고", "수도 중증장애/유공자 감면 파일을 추가하세요")
                return
            self.pushButton_16.setDisabled(True)
            self.pushButton_13.setDisabled(True)
            self.pushButton_15.setDisabled(False)
            self.pushButton_14.setDisabled(True)
        else:
            sname = '유공자'
            file = self.lineEdit_2.text()
            if '.xls' not in file or file == 0:
                QMessageBox.about(self, "경고", "수도 중증장애/유공자 감면 파일을 추가하세요")
                return
            self.pushButton_16.setDisabled(True)
            self.pushButton_13.setDisabled(True)
            self.pushButton_15.setDisabled(True)
            self.pushButton_14.setDisabled(False)
        
        with pd.ExcelFile(file) as f:
            code = sname
            sheet = self.sheet_select(f,code)
            df = pd.read_excel(f,sheet_name = sheet)
            header = df.columns.values.tolist()
        self.set_tbl(df, header)
        return

    def sheet_select(self, f, code):
        sheet_name = f.sheet_names
        for sheet in sheet_name:
            if code in sheet:
                return sheet
            else:
                pass




    def set_tbl(self, df, header):

        rdr_col = len(df.columns)
        rdr_row = len(df)
        self.tableWidget.clear()
        #self.tableWidget.setHorizontalHeaderLabels(header) # 파일이 바뀔경우 에러 발생 함
        # 따라서 데이터를 먼저 뿌리고 헤더를 뿌리도록 순서를 아래로 바꿈
        self.tableWidget.setRowCount(rdr_row)
        self.tableWidget.setColumnCount(rdr_col)
        for i in range(rdr_row):
            for j in range(rdr_col):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(df.iloc[i,j])))
                #self.setSectionResizeMode(j, QHeaderView.ResizeToContents)
        self.tableWidget.setHorizontalHeaderLabels(header)

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
        f5 = self.lineEdit_9.text()
        f6 = self.lineEdit_12.text()
        f7 = self.lineEdit_13.text()
        f8 = self.lineEdit_14.text()

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
        '''
        # 검증 파일 생성 확인
        if '.xls' not in f5 or f5 == 0:
            QMessageBox.about(self, "경고", "수도 기초수급 감면 파일을 확인하세요")
            return
        
        if '.xls' not in f6 or f6 == 0:
            QMessageBox.about(self, "경고", "수도 다자녀 감면 파일을 확인하세요")
            return
        
        if '.xls' not in f7 or f7 == 0:
            QMessageBox.about(self, "경고", "수도 중증장애인 감면 파일을 확인하세요")
            return
        
        if '.xls' not in f8 or f8 == 0:
            QMessageBox.about(self, "경고", "수도 유공자 감면 파일을 확인하세요")
            return
        '''

        df2 = self.welfare_calc(f1)
        df = df2[0]
        #df.rename(columns = {'복지코드' : '기초'}, inplace = True)
        df_f = df2[1]
        #df_f.rename(columns = {'복지코드' : '가족'}, inplace = True)

        df_temp = self.merits_calc(f2)
        df3 = df_temp[0]
        #df3.rename(columns = {'복지코드' : '중증'}, inplace = True)
        df4 = df_temp[1]
        #df4.rename(columns = {'복지코드' : '유공'}, inplace = True)
        discount = self.template_make(f3,df,df_f,df3,df4)
        
        self.pd_save(discount,f4)
        return

    def welfare_calc(self, f1):
        f = pd.ExcelFile(f1)
        d = self.seperate_dongho(f)
        df = d[0]
        df_f = d[1]
        total_복지 = len(df)
        self.lineEdit_5.setText(str(f'{total_복지:>7,}'))
        total_대가족 = len(df_f)
        self.lineEdit_6.setText(str(f'{total_대가족:>7,}'))
        return df, df_f

    def merits_calc(self, f2):
        # # 수도 유공자할인 등록
        f = pd.ExcelFile(f2)
        df = self.seperate_dongho(f)
        df_3 = df[0]
        total_중증 = len(df_3)
        self.lineEdit_7.setText(str(f'{total_중증:>7,}'))
        #df_4["유공자"]= '2'
        df_4 = df[1]
        total_유공자 = len(df_4)
        self.lineEdit_8.setText(str(f'{total_유공자:>7,}'))

        return df_3, df_4

    def seperate_dongho(self, f):
        sheet_name = f.sheet_names
        sheet_data = []
        for sheet in sheet_name:
            items_code = self.code_verify(sheet)
            df__ = pd.read_excel(f,sheet_name = sheet)
            cols = df__.columns
            if cols[0] == 'No':
                rows = -1
            else:
                s = df__.index[(df__["Unnamed: 0"] == "No")].tolist()
                rows = s[0]
            sheet = pd.ExcelFile.parse(f, sheet_name=sheet,header=0,skiprows=rows+1)
            header = sheet.columns.values.tolist() #dataframe에서 header list 작성
            for h in header:
                if '동호수' in h:
                    h_index = header.index(h)
                else:
                    pass
            try:
                temp = sheet[header[h_index]].str.split('-', expand = True)
                sheet['동'] = temp[0]
                sheet['호'] = temp[1]
                df_1 = sheet[['동', '호']]
            except:
                temp = sheet[header[h_index]].str.split('동 ', expand = True)
                sheet['동'] = temp[0]
                temp_1 = temp[1].str.slice(stop = -1)
                sheet['호'] = temp_1
                df_1 = sheet[['동', '호']]
            df_1[items_code['item']] = items_code['code']
            sheet_data.append(df_1)

        return sheet_data

    def code_verify(self, sheet):
        if '복지' in sheet:
            code = {'item':'복지', 'code':'3'}
            return code
        elif '다자녀' in sheet:
            code = {'item':'다자녀', 'code':'I'}
            return code
        elif '유공자' in sheet:
            code = {'item':'유공', 'code':'2'}
            return code
        else:
            code = {'item':'중증', 'code':'T'}
            return code

    def template_make(self, f3,df,df_f,df_3,df_4):
        dis = pd.merge(df, df_f, how = 'outer', on = ['동','호'])
        dis1 = pd.merge(dis, df_3, how = 'outer', on = ['동','호'])
        dis2 = pd.merge(dis1, df_4, how = 'outer', on = ['동','호'])
        # 종류별 concatnate 문자열 처리를 위하여 fill nan 처리 
        dis2.fillna('', inplace=True)
        dis2['Code'] = dis2['복지'].str.cat(dis2[['다자녀','중증','유공']])
       # 4개 조건을 조합하기 위하여 코드 합하기 및 길이가 2이상인 데이터 처리
        dis2.loc[dis2['Code'].str.len()>1, 'Code'] = 'V'
        dis3 = dis2[['동','호','Code']]

        v_count = len(dis3[dis3['Code']=='V'])
        count = dis3['Code'].count()
        self.lineEdit_10.setText(str(f'{v_count:>7,}')) # 중복
        self.lineEdit_11.setText(str(f'{count:>7,}')) # 총합계

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