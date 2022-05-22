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
    ]


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
        self.comboBox_9.activated.connect(self.comboBox_9Activated)
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
        self.out_file_to_table(df)
        self.out_dongho()
        self.comboBox_8.clear()
        self.comboBox_8.addItems(['공용','세대'])
        self.comboBox_9Init()
        
    def addOutMaterialToTable(self):
        
        data = []
        data.append(self.dateEdit_6.text())
        data.append(self.comboBox_10.currentText())
        data.append(self.comboBox_11.currentText())
        data.append(self.comboBox_8.currentText())
        data.append(self.comboBox_9.currentText())
        data.append(self.comboBox_7.currentText())
        if len(self.lineEdit_6.text())==0:
            data.append('**')
        else:
            data.append(self.lineEdit_6.text())
        print(data)

        self.set_tbl_6(data)
    
        def on_stock(self):
            dfIn = self.in_df()
            df_in = dfIn[['품명','규격', '입고수량']].copy()
            df_in_sum = df_in.groupby(['품명','규격']).sum()

            dfOut = self.out_df()
            df_out = dfOut[['품명','규격', '사용수량']].copy()
            df_out_sum = df_out.groupby(['품명','규격']).sum()

            df_on_stock = pd.merge(df_in_sum, df_out_sum, how = 'outer', on = ['품명','규격'])
            df_on_stock.fillna(0, inplace=True)
            df_on_stock['재고'] = df_on_stock['입고수량'] - df_on_stock['사용수량']
            print(df_on_stock)
            return df_on_stock
    
    def set_tbl_6(self,data):
        rowCount = self.tableWidget_6.rowCount()
        print(rowCount)
        self.tableWidget_6.setRowCount(rowCount+1)
        self.tableWidget_6.setColumnCount(len(data))
        c = 0
        for i in data:
            self.tableWidget_6.setItem(rowCount, c, QTableWidgetItem(i))
            c = c+1
        self.table_display()

    def out_file_to_table(self, df):

        df[['사용수량', '단가','재고수량']] = df[['사용수량', '단가','재고수량']].astype('str')
        df.fillna(' ')
        list = df.values.tolist()

        for d in list:
            self.set_tbl_6(d)
        self.tableWidget_5.scrollToBottom
        self.table_display()
    
    def out_df(self):
        file = r'C:\source\pygame\Nado Game\pyqt5\자재관리\사용대장.xlsx'
        with pd.ExcelFile(file) as f:
            df = pd.read_excel(f,skiprows=0)
        return df

    def in_df(self):
        file = r'C:\source\pygame\Nado Game\pyqt5\자재관리\입고대장.xlsx'
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

    def comboBox_9Init(self):
        df = self.in_df_make()
        items = df['품명'].unique()
        self.comboBox_9.clear()
        self.comboBox_9.addItems(items)
        df1 = df[(df['품명'] == self.comboBox_9.currentText())]
        spec = df1['규격'].unique()
        self.comboBox_7.clear()
        self.comboBox_7.addItems(spec)

    def comboBox_9Activated(self):
        df = self.in_df_make()
        items = df['품명'].unique()
        df1 = df[(df['품명'] == self.comboBox_9.currentText())]
        spec = df1['규격'].unique()
        self.comboBox_7.clear()
        self.comboBox_7.addItems(spec)

    def out_df_make(self):
        file = r'C:\source\pygame\Nado Game\pyqt5\자재관리\사용대장.xlsx'
        with pd.ExcelFile(file) as f:
            df = pd.read_excel(f,skiprows=0)
        return df

    def in_df_make(self):
        file = r'C:\source\pygame\Nado Game\pyqt5\자재관리\입고대장.xlsx'
        with pd.ExcelFile(file) as f:
            df = pd.read_excel(f,skiprows=0)
        return df
    
    def comboBox_5Activated(self):
        df = self.in_df_make()
        df = df[(df['품명'] == self.comboBox_5.currentText())]
        items = df['품명'].unique()
        spec = df['규격'].unique()
        self.comboBox_6.clear()
        self.comboBox_6.addItems(spec)

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