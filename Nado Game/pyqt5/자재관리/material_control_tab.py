import sys
import os
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal,QDate
from PyQt5 import uic
from datetime import datetime

def resource_path(relative_path):
    base_path = getattr(sys, "_MAIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form = resource_path("mate_main_window.ui")
form_class = uic.loadUiType(form)[0]
#form_1 = resource_path("elec_file_verify.ui")
#form_class_1 = uic.loadUiType(form_1)[0]

now = datetime.now()
yyyymm = now.strftime("%Y")+now.strftime("%m")+'월'
yyyy = now.strftime("%Y")

LE =  [
    'C:/source/pygame/Nado Game/pyqt5/자재관리/입고대장.xlsx',
    'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/한전부과자료',
    'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/한전부과자료',
    'D:/과장/1 1 부과자료/'+yyyy+'년/Templates/Elec_Template_File_for_XPERP_upload.xls',
    'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/xperp_감면자료',
    'D:/과장/1 1 부과자료/'+yyyy+'년/Templates/xperp_code_comparasion_table.xlsx'
    ]

'''class ElWidget(QDialog, form_class_1):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        elWindow = ElWindow()

        self.tableWidget.setRowCount(28)
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setHorizontalHeaderLabels(['기존', '금월'])
        self.tableWidget.setSortingEnabled(True) # default ; False
        
        self.pushButton_6.clicked.connect(self.close)
        self.pushButton_7.clicked.connect(self.item_verify)
        self.pushButton_8.clicked.connect(self.kind_verify)
        self.pushButton_9.clicked.connect(self.tableWidget.scrollToTop)
        self.pushButton_10.clicked.connect(self.tableWidget.scrollToBottom)
        self.show()

    def set_tbl(self, data):

        rdr_col = len(data)
        temp_rdr_row = []
        for d in data:
            temp = len(d)
            temp_rdr_row.append(temp) 
        rdr_row = max(temp_rdr_row)
        self.tableWidget.clear()
        self.tableWidget.setRowCount(rdr_row)
        self.tableWidget.setColumnCount(rdr_col)
        c = 0
        for i in data:
            r = 0
            c = c+1
            for j in i:
                r = r+1
                self.tableWidget.setItem(r-1, c-1, QTableWidgetItem(j))
        # self.tableWidget.setHorizontalHeaderLabels(['기존', '금월'])
        headers = ['기존', '금월']
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
        #app.exec_()

    def item_verify(self):
        f1 = elWindow.lineEdit.text()
        if '.xls' not in f1 or f1 == 0:
            QMessageBox.about(self, "경고", "한전 복지감면 파일을 추가하세요")
            return
        df = pd.read_excel(f1,skiprows=2)#, dtype={'동':int, '호':int}) #,thousands=',')
        df_col_names = df.columns.tolist()
        used_col_names = ['동', '호', '동호명', '가구수', '계약\n종별', '요금적용\n전력', '사용량', '기본요금', '전력량\n요금', 
            '연료비조정\n요금', '필수사용\n공제', '복지추가\n감액', '할인\n구분', '복지할인', '요금개편\n차액', 
            '절전할인', '자동이체\n/인터넷', '단수', '전기요금', '부가세', '전력\n기금', '전기\n바우처', '정산', '출산가구소급', 
            '당월소계', 'TV수신료', '청구금액']

        sub_list = list(set(df_col_names) ^ set(used_col_names))
        data = [used_col_names]
        data.append(df_col_names)
        self.set_tbl(data)
        self.textEdit.clear()
        for s in sub_list:
            self.textEdit.append(str(s))
        return

    def kind_verify(self):
        f2 = elWindow.lineEdit_2.text()
        if '.xls' not in f2 or f2 == 0:
            QMessageBox.about(self, "경고", "한전 감면 종류 파일을 추가하세요")
            return
        df_w = pd.read_excel(f2,skiprows=2, thousands=',')#, dtype={'동':int, '호':int}) #,thousands=',')
        
        df_col = df_w.columns.to_list()
        try:
            kind_of_welfare = list(df_w['장애종류'].unique())
        except:
            QMessageBox.about(self, "경고", "'장애종류' 키값이 없습니다. 파일을 확인하세요")
            return
        new = ['파일 항목','']+df_col +['','할인 종류','']+kind_of_welfare

        new_col_names = ['동', '호', '대상자명','할인종류','장애종류','장애등급','할인요금']
        used_kind_of_welfare = ['장애인 할인', '다자녀 할인', '대가족 할인', '의료기기 할인', '기초수급 할인', '출산가구 할인', '복지추가감액',
                                '기초수급 할인 (주거, 교육)', '차상위계층 할인', '사회복지 할인', '독립유공 할인']
        old = ['파일 항목','']+new_col_names +['','할인 종류','']+ used_kind_of_welfare
        data = []
        data.append(old)
        data.append(new)
        sub_list = list(set(old) ^ set(new))
        self.set_tbl(data)
        self.textEdit.clear()
        for s in sub_list:
                self.textEdit.append(str(s))
        return
        '''

class ElWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.LE = LE
        self.setupUi(self)

        # 자재입고 입력 init setup
        self.dateEdit_5.setDate(QDate.currentDate())
        self.dateEdit_5.setCalendarPopup(True)
        self.dateEdit_6.setDate(QDate.currentDate())
        self.dateEdit_6.setCalendarPopup(True)
        self.init_in_data_make()
        self.init_out_data_make()
        
        #items_data = data[0]
        #['독립유공 할인', '국가유공 할인', '민주유공 할인', '장애인 할인', '사회복지 할인', '기초수급 할인', '기초수급 할인 (주거/교육)', '차상위계층 할인']
        #spec_data=data[1]
        #['대가족 할인', '출산가구 할인', '다자녀 할인', '의료기기 할인']
        self.comboBox_5.activated.connect(self.comboBox_5Activated)
        self.comboBox_9.activated.connect(self.comboBox_5Activated)
        self.comboBox_10.activated.connect(self.out_dongho)
        self.pushButton.clicked.connect(self.addComboBoxItem)
        self.pushButton_2.clicked.connect(self.addComboBoxSpecItem)
        self.pushButton_7.clicked.connect(self.inTableToSaveExcelFile)
        self.pushButton_6.clicked.connect(self.addInMaterialToTable)
        self.pushButton_11.clicked.connect(self.addOutMaterialToTable)
        self.lineEdit.textChanged.connect(self.lineEditChanged)
        self.lineEdit_2.textChanged.connect(self.lineEdit_2Changed)

        '''self.lineEdit.setText(LE[0])
        self.lineEdit_2.setText(LE[1])
        self.lineEdit_3.setText(LE[2])
        self.lineEdit_4.setText(LE[3])
        self.lineEdit_15.setText(LE[4])
        self.label_5.setText('프로그램 작성 : 임훈택 Rev 0, 2022.05.11 Issued')

        self.pushButton.clicked.connect(self.add_file)
        self.pushButton_2.clicked.connect(self.add_file)
        self.pushButton_3.clicked.connect(self.add_file)
        self.pushButton_4.clicked.connect(self.add_file)
        self.pushButton_8.clicked.connect(self.add_file)
        self.pushButton_5.clicked.connect(self.start)
        self.pushButton_6.clicked.connect(self.close)
        self.pushButton_7.clicked.connect(self.my_window)
    '''
    
    def init_out_data_make(self):
        df = self.out_df()
        self.set_tbl_6(df)
        self.out_dongho()
        self.comboBox_8.clear()
        self.comboBox_8.addItems(['공용','세대'])
        data = self.comboBox_5Activated()
        self.comboBox_9.clear()
        self.comboBox_9.addItems(data[0])
        self.comboBox_7.clear()
        self.comboBox_7.addItems(data[1])

        
    
    
    def addOutMaterialToTable(self):
        
        in_data = []
        in_data.append(self.dateEdit_6.text())
        in_data.append(self.comboBox_10.currentText())
        in_data.append(self.comboBox_11.currentText())
        in_data.append(self.comboBox_8.currentText())
        in_data.append(self.comboBox_9.currentText())
        in_data.append(self.comboBox_7.currentText())
        if len(self.lineEdit_6.text())==0:
            in_data.append('**')
        else:
            in_data.append(self.lineEdit_6.text())

        self.set_tbl_6(in_data)
    
    
    
    def set_tbl_6(self,data):
        rowCount = self.tableWidget_6.rowCount()
        print(rowCount)
        rdr_col = len(data)
        rdr_row = 1
        #self.tableWidget_5.clear()
        self.tableWidget_6.setRowCount(rowCount+1)
        self.tableWidget_6.setColumnCount(len(data))
        c = 0
        for i in data:
            # r = 0
            self.tableWidget_6.setItem(rowCount, c, QTableWidgetItem(i))
            c = c+1

            #for j in i:
            #    r = r+1
        # self.tableWidget.setHorizontalHeaderLabels(['기존', '금월'])
        self.table_display()
    
    def out_df(self):
        file = r'C:\source\pygame\Nado Game\pyqt5\자재관리\사용대장.xlsx'
        with pd.ExcelFile(file) as f:
            df = pd.read_excel(f,skiprows=0)
        return df


    def dong_ho(self):
        file = r'C:\source\pygame\Nado Game\pyqt5\자재관리\동호대장.xlsx'
        with pd.ExcelFile(file) as f:
            df = pd.read_excel(f,skiprows=0)
            df[['동','호']] = df[['동','호']].astype('str')
        return df

    def out_dongho(self):
        df = self.dong_ho()
        dong = df['동'].unique()
        self.comboBox_11.clear()
        self.comboBox_10.addItems(dong)
        ho = df['호'].unique()
        df1 = df[(df['동'] == self.comboBox_10.currentText())]
        current_ho = df1['호'].unique()
        self.comboBox_11.clear()
        self.comboBox_11.addItems(current_ho)

    def comboBox_9Activated(self):
        data = self.comboBox_5Activated()
        self.comboBox_9.addItems(data[0])
        self.comboBox_7.addItems(data[1])
    
    
    
    def comboBox_5Activated(self):
        file = LE[0]#r'C:\source\pygame\Nado Game\pyqt5\자재관리\입고대장.xlsx'
        with pd.ExcelFile(file) as f:
            df = pd.read_excel(f,skiprows=0)
            df.fillna('')
        df1 = df[(df['품명'] == self.comboBox_5.currentText())]
        items = df['품명'].unique()
        spec = df1['규격'].unique()
        self.comboBox_6.clear()
        self.comboBox_6.addItems(spec)
        df2= df[(df['품명'] == self.comboBox_9.currentText())]
        spec_out = df2['규격'].unique()
        return items, spec_out

    def init_in_data_make(self):
        file = LE[0]#r'C:\source\pygame\Nado Game\pyqt5\자재관리\입고대장.xlsx'
        with pd.ExcelFile(file) as f:
            df = pd.read_excel(f,skiprows=0)
        items = df['품명'].unique()
        spec = df['규격'].unique()
        self.comboBox_5.addItems(items)
        self.comboBox_6.addItems(spec)
        df[['입고수량', '구입금액','단가']] = df[['입고수량', '구입금액','단가']].astype('str')
        df.fillna(' ')
        list = df.values.tolist()

        for d in list:
            self.set_tbl(d)
        self.table_display()

        self.tableWidget_5.scrollToBottom

    def inTableToSaveExcelFile(self):
        file = LE[0]#r'C:\source\pygame\Nado Game\pyqt5\자재관리\입고대장.xlsx'
        #with pd.ExcelFile(file) as f:
        #    sheet = self.sheet_select(f,code)
        df = self.data_query()
        #f_split = file.split('.')
        #file = f_split[0]+sheet+'.'+f_split[1]
        
        if os.path.isfile(file):
            os.remove(file)
            df.to_excel(file,index=False,header=True)
        else:
            df.to_excel(file,index=False,header=True)
        
        return 

    def data_query(self):
        '''
        data query from tablewidget to pandas dataframe
        '''
        rowcount = self.tableWidget_5.rowCount()
        colcount = self.tableWidget_5.columnCount()
        
        headers = [self.tableWidget_5.horizontalHeaderItem(x).text() for x in range(0,colcount)]
        print(headers)
        data_list = []
        for i in range(0, rowcount):
            data =[]
            for j in range(0, colcount):
                d = self.tableWidget_5.item(i,j).text()
                data.append(d)
            data_list.append(data)
        df = pd.DataFrame(data_list) # list to dataframe
        print(df)
        df.columns = headers # set the hwaders on dataframe
        
        return df

    def lineEditChanged(self):
        try:
            if len(self.lineEdit_2.text())==0:
                pass

        except:
            in_qty = self.lineEdit.text()
            in_price = self.lineEdit_2.text()
            unit_p = str(round(int(in_price)/int(in_qty)))
            self.lineEdit_3.setText(unit_p)
            return

    def lineEdit_2Changed(self):
        try:
            in_qty = self.lineEdit.text()
            in_price = self.lineEdit_2.text()
            unit_p = str(round(int(in_price)/int(in_qty)))
            self.lineEdit_3.setText(unit_p)
        except:
            QMessageBox.about(self, "경고", "가격 및 수량 자료를 입력하세요")
            return

    def addComboBoxItem(self) :
        self.comboBox_5.addItem(self.lineEdit_5.text())
        print("Item Added")
    
    def addComboBoxSpecItem(self) :
        self.comboBox_6.addItem(self.lineEdit_8.text())
        print("Item Added")
    
    def addInMaterialToTable(self):
        
        in_data = []
        in_data.append(self.dateEdit_5.text())
        in_data.append(self.comboBox_5.currentText())
        in_data.append(self.comboBox_6.currentText())
        if len(self.lineEdit.text())==0:
            QMessageBox.about(self, "경고", "수량 자료를 입력하세요")
            return
        else:
            in_data.append(self.lineEdit.text())
        if len(self.lineEdit_2.text())==0:
            QMessageBox.about(self, "경고", "가격 자료를 입력하세요")
            return
        else:
            in_data.append(self.lineEdit_2.text())
        in_data.append(self.lineEdit_3.text())
        if len(self.lineEdit_4.text())==0:
            in_data.append('**')
        else:
            in_data.append(self.lineEdit_4.text())
        if len(self.lineEdit_6.text())==0:
            in_data.append('**')
        else:
            in_data.append(self.lineEdit_6.text())
        print(in_data)

        self.set_tbl(in_data)
    
    
    def set_tbl(self,data):
        #data = ['2022-05-21', '독립유공 할인', '대가족 할인', '120', '45789', '382', 'as', 'S']
        rowCount = self.tableWidget_5.rowCount()
        #self.tableWidget_5.insertRow(rowCount)
        print(rowCount)
        rdr_col = len(data)
        rdr_row = 1
        #self.tableWidget_5.clear()
        self.tableWidget_5.setRowCount(rowCount+1)
        self.tableWidget_5.setColumnCount(len(data))
        c = 0
        for i in data:
            # r = 0
            self.tableWidget_5.setItem(rowCount, c, QTableWidgetItem(i))
            c = c+1

            #for j in i:
            #    r = r+1
        # self.tableWidget.setHorizontalHeaderLabels(['기존', '금월'])
        self.table_display()

    def table_display(self):
        headers = ['입고일', '품명','규격','입고수량','구입금액','단가','구입업체','비고']
        self.tableWidget_5.setHorizontalHeaderLabels(headers)
        header = self.tableWidget_5.horizontalHeader()
        twidth = header.width()
        width = []
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            width.append(header.sectionSize(column))
        
        wfactor = int(twidth / sum(width))
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            header.resizeSection(column, width[column]*wfactor)
        self.tableWidget_5.scrollToBottom
        
    
    
    def my_window(self):
        elwidget = ElWidget()
        elwidget.exec_()

    @pyqtSlot()
    def add_file(self):

        sname = self.sender().text()

        if sname == '복지할인':
            init_dir = self.LE[0]
            fname = QFileDialog.getOpenFileName(self, '엑셀 데이타 파일을 선택하세요', init_dir, 'All Files (*) :: Excel (*.xls *.xlsx)')
            if len(fname[0]) != 0:
                self.lineEdit.setText(fname[0])
            else:
                self.lineEdit.setText(LE[0])

        elif sname == '할인종류':
            init_dir = self.LE[1]
            fname = QFileDialog.getOpenFileName(self, '엑셀 데이타 파일을 선택하세요', init_dir, 'All Files (*) :: Excel (*.xls *.xlsx)')
            if len(fname[0]) != 0:
                self.lineEdit_2.setText(fname[0])
            else:
                self.lineEdit_2.setText(LE[1])
        
        elif sname == 'Code Table':
            init_dir = self.LE[4]
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
        f5 = self.lineEdit_15.text()

        # 파일 목록 확인
        if '.xls' not in f1 or f1 == 0:
            QMessageBox.about(self, "경고", "한전 복지감면 파일을 추가하세요")
            return
        
        if '.xls' not in f2 or f2 == 0:
            QMessageBox.about(self, "경고", "한전 감면 종류 파일을 추가하세요")
            return

        if '.xls' not in f5 or f5 == 0:
            QMessageBox.about(self, "경고", "한전 감면 종류 파일을 추가하세요")
            return

        if '.xls' not in f3 or f3 == 0:
            QMessageBox.about(self, "경고", "Template File을 추가하세요")
            return

        # 저장 경로 확인
        if f4 == 0:
            QMessageBox.about(self, "경고", "저장 경로를 선택하세요")
            return

        df2 = self.welfare_calc(f1)
        subset_df = self.kind_calc(f2)
        subset_df_w = subset_df[0]
        subset_df_f = subset_df[1]
        discount = self.discount_file(f3,df2,subset_df_w,subset_df_f)
        self.pd_save(discount[0],f4)
        return

    def welfare_calc(self, f1):
        df = pd.read_excel(f1,skiprows=2)#, dtype={'동':int, '호':int}) #,thousands=',')
        df.dropna(subset=['동', '호'],inplace=True)
        col_sel =['동','호', '필수사용\n공제','복지추가\n감액']
        필수사용공제 = df[col_sel[2]].sum()
        복지추가감액 = df[col_sel[3]].sum()
        df1= df[col_sel].copy()
        df1['sum'] = df1[col_sel[2]] + df1[col_sel[3]]
        df1[col_sel[2]] = df1['sum']
        df1[col_sel[:3]] = df1[col_sel[:3]].astype('int')
        df2 = df1[col_sel[:3]].copy()
        return df2, 필수사용공제, 복지추가감액

    def code_dict_make(self, kind_code):
        file = self.lineEdit_15.text()
        # file = r'E:\source\pygame\Nado Game\pyqt5\감면자료\xperp code comparasion table.xlsx'
        with pd.ExcelFile(file) as f:
            df = pd.read_excel(f, sheet_name = 1)
        sheet = f.sheet_names
        df.dropna(inplace = True)
        code_dict = []
        for c in kind_code:
            is_elec = df['분류'] == c
            df_elec = df[is_elec]
            kind_list = df_elec['종류'].tolist()
            code_list = df_elec['코드'].tolist()
            kind_dict = dict(zip(kind_list, code_list))
            code_dict.append(kind_list)
            code_dict.append(code_list)
            code_dict.append(kind_dict)
        return code_dict

    def df_create(self, f1):
        df = pd.read_excel(f1,skiprows=2)
        df.dropna(subset=['동', '호'],inplace=True)
        con = df[df['할인종류'].str.contains('추가복지감액')].index
        df.drop(con, inplace=True)
        df_w = df[['동', '호','할인종류','할인요금']].copy()
        return df_w

    def kind_calc(self, f1):
        df = self.df_create(f1)
        code = ['가족','복지']
        code_dict = self.code_dict_make(code)
        kind_list = [code_dict[0],code_dict[3]]
        kind_dict = [code_dict[2],code_dict[5]]
        df_list = []
        for i in range(len(kind_list)):
            df_1 = df[df['할인종류'].isin(kind_list[i])].copy()
            for kind, code in kind_dict[i].items():
                df_1.loc[df_1.할인종류 == kind, '복지코드'] = code
            df_1.set_index(['동','호'],inplace=True)
            df_list.append(df_1)
        return df_list

    def discount_file(self, f3,df2,subset_df_f,subset_df_w):
        
        df_x = pd.read_excel(f3,skiprows=0)
        
        # xperp upload template 양식의 columns list 생성
        # 동호를 indexing하여 dataFrame merge 준비
        
        df_x.set_index(['동','호'],inplace=True)
        # discount df 생성 (Template df(df_x)에 필수사용공제(df2) merge
        
        discount = pd.merge(df_x, df2[0], how = 'outer', on = ['동','호'])
        # discount = pd.merge(discount, subset_df_a, how = 'outer', on = ['동','호'])

        # 사용량 보장공제를 한전금액(필수사용공제) Data로 Update
        discount['사용량보장공제'] = discount['필수사용\n공제']
        
        # 사용량 보장공제 임시데이터 columns를 drop
        discount = discount.drop(['필수사용\n공제'],axis=1)
        
        # Template df에 필수사용공제 merge
        discount = pd.merge(discount, subset_df_f, how = 'outer', on = ['동','호'])
        discount['대가족할인액'] = discount['할인요금']
        discount['대가족할인구분'] = discount['복지코드']
        discount = discount.drop(['복지코드','할인요금','할인종류'],axis=1)
        discount = pd.merge(discount, subset_df_w, how = 'outer', on = ['동','호'])

        #discount1 = discount.reset_index()
        discount['복지할인액'] = discount['할인요금']
        discount['복지할인구분'] = discount['복지코드']
        discount = discount.drop(['복지코드','할인요금','할인종류'],axis=1)
        
        total_사용량보장공제 = int(discount['사용량보장공제'].sum())
        total_대가족할인액 = int(discount['대가족할인액'].sum())
        total_복지할인액 = int(discount['복지할인액'].sum())
        sub_total = int(total_대가족할인액 + total_복지할인액)
        grand_total = int(sub_total + total_사용량보장공제)
        # display the result of computation
        self.lineEdit_5.setText(str(f'{total_사용량보장공제:>20,}'))
        self.lineEdit_6.setText(str(f'{total_대가족할인액:>20,}'))
        self.lineEdit_7.setText(str(f'{total_복지할인액:>20,}'))
        self.lineEdit_8.setText(str(f'{df2[1]:>20,}'))
        self.lineEdit_9.setText(str(f'{df2[2]:>20,}'))
        self.lineEdit_10.setText(str(f'{sub_total:>20,}'))
        self.lineEdit_11.setText(str(f'{grand_total:>20,}'))

        return discount, total_사용량보장공제, total_대가족할인액, total_복지할인액

    def pd_save(self, discount,f4):

        #작업월을 파일이름에 넣기 위한 코드 (작업일 기준)
        now = datetime.now()
        dt1 = now.strftime("%Y")+now.strftime("%m")
        dt1 = dt1+'ELEC_XPERP_Upload_J_K_R_S_T_columns.xlsx'
        file_name = f4+'/'+dt1

        #file save
        try:
            if os.path.isfile(file_name):
                os.remove(file_name)
                discount.to_excel(file_name,index=False,header=True)
            else:
                discount.to_excel(file_name,index=False,header=True)
        except:
            QMessageBox.about(self, "경고", "파일을 사용하고 있습니다. 파일을 닫아주세요.")
            
        
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
    elWindow = ElWindow()
    elWindow.show()
    app.exec_()