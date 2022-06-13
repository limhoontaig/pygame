import sys
import os
import pandas as pd
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QDialog, QFileDialog, QApplication,QMainWindow, QMessageBox
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal
from PyQt5 import uic
from datetime import datetime

def resource_path(relative_path):
    base_path = getattr(sys, "_MAIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form = resource_path("water_separate_mainwindow.ui")
form_class = uic.loadUiType(form)[0]
form1 = resource_path("water_file_verify.ui")
form_class1 = uic.loadUiType(form1)[0]

# constants
now = datetime.now()
yyyymm = now.strftime("%Y")+now.strftime("%m")+'월'
yyyy = now.strftime("%Y")

LE =  [
    'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/수도감면자료',
    'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/수도감면자료',
    'D:/과장/1 1 부과자료/'+yyyy+'년/Templates/Water_Template_File_for_XPERP_upload.xls',
    'D:/과장/1 1 부과자료/'+yyyy+'년/Templates/xperp_code_comparasion_table.xlsx',
    'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/xperp_감면자료'
    ]

class MyWidget(QDialog, form_class1):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        myWindow = MyWindow()
        self.tableWidget.setRowCount(28)
        self.tableWidget.setColumnCount(3)
        self.pushButton.clicked.connect(self.close)
        
        self.pushButton_7.clicked.connect(self.data_verify)
        self.pushButton_8.clicked.connect(self.data_verify)
        self.pushButton_11.clicked.connect(self.data_verify)
        self.pushButton_12.clicked.connect(self.data_verify)
        
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setHorizontalHeaderLabels(['No', '사용가번호', '동호수'])
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers) # QAbstractItemView.AllEditTriggers
        self.tableWidget.cellChanged.connect(self.cellchanged_event)
        self.tableWidget.setSortingEnabled(True) # default ; False
        self.pushButton_9.clicked.connect(self.tableWidget.scrollToTop)
        self.pushButton_10.clicked.connect(self.tableWidget.scrollToBottom)
        self.pushButton_16.clicked.connect(self.data_change_save)
        self.pushButton_15.clicked.connect(self.data_change_save)
        self.pushButton_13.clicked.connect(self.data_change_save)
        self.pushButton_14.clicked.connect(self.data_change_save)
        self.pushButton_16.setDisabled(True)
        self.pushButton_13.setDisabled(True)
        self.pushButton_15.setDisabled(True)
        self.pushButton_14.setDisabled(True)
        #self.show()

    def cellchanged_event(self, row, col):
        #df = self.data_query()
        #end_col = len(df.columns)
        #code = self.tableWidget.item(row,end_col).text()
        data = self.tableWidget.item(row,col)

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
        '''
        verified data save after the data to verify and modify on the tableWidget
        divided by code
        '''
        sname = self.sender().text()
        code = sname[:2]
        if code == '복지': # 코드 : 복지
            file = myWindow.lineEdit.text()
            file_code = self.table_to_pd_excel(file, code)
            myWindow.lineEdit_9.setText(file_code)

        elif code == '다자': # 코드 다자녀
            file = myWindow.lineEdit.text()
            file_code = self.table_to_pd_excel(file, code)
            myWindow.lineEdit_12.setText(file_code)
            
        elif code == '중증': # 코드 중증장애
            file = myWindow.lineEdit_2.text()
            file_code = self.table_to_pd_excel(file, code)
            myWindow.lineEdit_13.setText(file_code)

        else: # code in sname: # 코드 유공자
            file = myWindow.lineEdit_2.text()
            file_code = self.table_to_pd_excel(file, code)
            myWindow.lineEdit_14.setText(file_code)


    def table_to_pd_excel(self, file, code):
        
        with pd.ExcelFile(file) as f:
            sheet = self.sheet_select(f,code)
        df = self.data_query()
        f_split = file.split('.')
        file = f_split[0]+sheet+'.'+f_split[1]
        '''
        if os.path.isfile(file):
            os.remove(file)
            df.to_excel(file,sheet_name= sheet,index=False,header=True)
        else:
            df.to_excel(file,sheet_name= sheet,index=False,header=True)
        '''
        return file



    def data_verify(self):
        sname = self.sender().text()
        code = sname[:2]
        if code == '복지': # 코드 : 복지
            file = myWindow.lineEdit.text()
            if '.xls' not in file or file == 0:
                QMessageBox.about(self, "경고", "수도 다자녀/복지감면 파일을 추가하세요")
                return
            self.pushButton_16.setDisabled(False)
            self.pushButton_13.setDisabled(True)
            self.pushButton_15.setDisabled(True)
            self.pushButton_14.setDisabled(True)

        elif code == '다자':
            file = myWindow.lineEdit.text()
            if '.xls' not in file or file == 0:
                QMessageBox.about(self, "경고", "수도 다자녀/복지감면 파일을 추가하세요")
                return
            self.pushButton_16.setDisabled(True)
            self.pushButton_13.setDisabled(False)
            self.pushButton_15.setDisabled(True)
            self.pushButton_14.setDisabled(True)
        elif code == '중증':
            file = myWindow.lineEdit_2.text()
            if '.xls' not in file or file == 0:
                QMessageBox.about(self, "경고", "수도 중증장애/유공자 감면 파일을 추가하세요")
                return
            self.pushButton_16.setDisabled(True)
            self.pushButton_13.setDisabled(True)
            self.pushButton_15.setDisabled(False)
            self.pushButton_14.setDisabled(True)
        else:
            code = '유공'
            file = myWindow.lineEdit_2.text()
            if '.xls' not in file or file == 0:
                QMessageBox.about(self, "경고", "수도 중증장애/유공자 감면 파일을 추가하세요")
                return
            self.pushButton_16.setDisabled(True)
            self.pushButton_13.setDisabled(True)
            self.pushButton_15.setDisabled(True)
            self.pushButton_14.setDisabled(False)
        
        with pd.ExcelFile(file) as f:
            sheet = self.sheet_select(f,code)
            df = pd.read_excel(f,sheet_name = sheet)
            df['Code'] = code
            header = df.columns.values.tolist()
        self.set_tbl(df, header)
        f1 = myWindow.lineEdit.text()
        f2 = myWindow.lineEdit_2.text()
        if code == '복지' or code == '다자':
            self.textEdit.clear()
            self.textEdit.setText(f1)
        else:
            self.textEdit.clear()            
            self.textEdit.setText(f2)
        return

    def sheet_select(self, f, code):
        sheet_name = f.sheet_names
        for sheet in sheet_name:
            if code in sheet:
                return sheet
            else:
                pass

    def set_tbl(self, df, headers):

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
        self.tableWidget.setHorizontalHeaderLabels(headers)
        header = self.tableWidget.horizontalHeader()
        twidth = header.width()
        width = []
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            width.append(header.sectionSize(column))
        
        wfactor = int(twidth / sum(width))
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            header.resizeSection(column, width[column]*wfactor)
        


class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.LE = LE
        self.setupUi(self)
        self.lineEdit.setText(LE[0])
        self.lineEdit_2.setText(LE[1])
        self.lineEdit_3.setText(LE[2])
        self.lineEdit_15.setText(LE[3])
        self.lineEdit_4.setText(LE[4])
        self.label_5.setText('Program Developed by HoonTaig Lim, Rev 0 Issued, 2022.05.16')

        self.pushButton.clicked.connect(self.add_file)
        self.pushButton_2.clicked.connect(self.add_file)
        self.pushButton_3.clicked.connect(self.add_file)
        self.pushButton_8.clicked.connect(self.add_file)
        self.pushButton_4.clicked.connect(self.add_file)
        self.pushButton_5.clicked.connect(self.start)
        self.pushButton_7.clicked.connect(self.my_window)

        self.pushButton_6.clicked.connect(self.close)

    def my_window(self):
        mywidget = MyWidget()
        mywidget.exec_()
        

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
        
        elif sname == 'Code Table':
            init_dir = self.LE[3]
            fname = QFileDialog.getOpenFileName(self, '엑셀 데이타 파일을 선택하세요', init_dir, 'All Files (*) :: Excel (*.xls *.xlsx)')
            if len(fname[0]) != 0:
                self.lineEdit_15.setText(fname[0]) 
            else: 
                self.lineEdit_15.setText(LE[2])
        
        else:
            init_dir = self.LE[4]
            fname = QFileDialog.getExistingDirectory(self, '저장 Direttory를 선택하새요', init_dir)
            if len(fname) != 0:
                self.lineEdit_4.setText(fname)
            else:
                self.lineEdit_4.setText(LE[4])

    # 계산 시작
    def start(self):
        # 각 옵션들 값을 확인
        f1 = self.lineEdit.text()
        f2 = self.lineEdit_2.text()
        f3 = self.lineEdit_3.text()
        f4 = self.lineEdit_4.text()
        f5 = self.lineEdit_15.text()

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

        if '.xls' not in f5 or f5 == 0:
            QMessageBox.about(self, "경고", "Code Comparasion Table File을 추가하세요")
            return

        # 저장 경로 확인
        if f4 == 0:
            QMessageBox.about(self, "경고", "저장 경로를 선택하세요")
            return

        files = [f1,f2]
        sheet_names = self.sheet_list(files)
        df, df_c, df_f, df_f_c, df3, df3_c, df4, df4_c = self.seperate_dongho(sheet_names)
        #df, df_c, df_f, df_f_c, df3, df3_c, df4, df4_c 
        total_복지 = len(df)
        self.lineEdit_5.setText(str(f'{total_복지:>7,}'))

        total_대가족 = len(df_f)
        self.lineEdit_6.setText(str(f'{total_대가족:>7,}'))

        total_중증 = len(df3)
        self.lineEdit_7.setText(str(f'{total_중증:>7,}'))

        total_유공자 = len(df4)
        self.lineEdit_8.setText(str(f'{total_유공자:>7,}'))

        discount = self.template_make(f3,df,df_f,df3,df4,df_c,df_f_c,df3_c,df4_c)
        self.pd_save(discount,f4)
        return

    def sheet_list(self, files):
        sheets =[]
        for f in files:
            file = pd.ExcelFile(f)
            sheet_name = file.sheet_names
            for s in sheet_name:
                c = self.code_make(s)
                s = [file, s, c]
                sheets.append(s)
        return sheets

    def seperate_dongho(self, file):
        df_data = []
        for f, sheet,code in file:
            c_d = self.code_dict(['수도감면'])
            code_dict = c_d[0][1]
            rows = self.skip_row(f,sheet) 
            df = pd.ExcelFile.parse(f, sheet_name=sheet,header=0,skiprows=rows+1)
            header = df.columns.values.tolist() #dataframe에서 header list 작성
            for h in header:
                if '동호수' in h:
                    h_index = header.index(h)
                    df['dongho'] =df[h].str.findall('(\d{3,4})')
                    df['동'] =df['dongho'].str[0]
                    df['호'] =df['dongho'].str[1]
                else:
                    pass
            df_1 = df[['동', '호']].copy()
            df_1[code] = code_dict[code]
            df_data.append(df_1)
            df_data.append(code)

        return df_data

    def skip_row(self,f,sheet):
        df = pd.read_excel(f,sheet_name = sheet)
        cols = df.columns
        if cols[0] == 'No':
            rows = -1
        else:
            s = df.index[(df["Unnamed: 0"] == "No")].tolist()
            rows = s[0]
        return rows

    def code_dict(self, div):
        f5 = self.lineEdit_15.text()
        with pd.ExcelFile(f5) as f:
            df = pd.read_excel(f,sheet_name=1, skiprows=0)
        df.dropna(inplace=True)

        df['종별분류'] = df['종별'].str.cat(df[['분류']])
        kind_div = []
        kind = df['종별분류'].unique()
        for k in div:
            kind_div.append(k) 
        code_dict = []
        for kind in kind_div:
            df1 = df[(df['종별분류'] == kind)]
            string_list = df1['종류'].tolist()
            int_list = df1['코드'].tolist()
            kind = [kind]
            kind_dict = dict(zip(string_list, int_list))
            kind.append(kind_dict)
            code_dict.append(kind)
            
        return code_dict

    def code_make(self, sheet):
        
        if '복지' in sheet:
            code = '기초생활'
            return code
        elif '다자녀' in sheet:
            code = '다자녀'
            return code
        elif '유공자' in sheet:
            code = '유공자'
            return code
        else:
            code = '중증장애'
            return code

    def template_make(self, f3,df,df_f,df_3,df_4,df_c,df_f_c,df3_c,df4_c):
        dis = pd.merge(df, df_f, how = 'outer', on = ['동','호'])
        dis1 = pd.merge(dis, df_3, how = 'outer', on = ['동','호'])
        dis2 = pd.merge(dis1, df_4, how = 'outer', on = ['동','호'])
        # 종류별 concatnate 문자열 처리를 위하여 fill nan 처리 
        dis2.fillna('', inplace=True)

        dis2['Code'] = dis2[df_c].str.cat(dis2[[df_f_c,df3_c,df4_c]])
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
        '''
        dttemp = file_name.split('.')
        dt2 = dttemp[0] + '.xls'

        if os.path.isfile(dt2):
            os.remove(dt2)
            os.rename(file_name, dt2)   
        else:
            os.rename(file_name, dt2)
        '''
        return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()