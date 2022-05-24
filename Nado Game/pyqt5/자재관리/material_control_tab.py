import sys
import os
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal,QDate
from PyQt5 import uic
from datetime import datetime

def resource_path(relative_path):
    base_path = getattr(sys, "_MAIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form = resource_path("mate_main_window.ui")
form_class = uic.loadUiType(form)[0]

now = datetime.now()
yyyymm = now.strftime("%Y")+now.strftime("%m")+'월'
yyyy = now.strftime("%Y")

if os.path.isfile(r'E:\source\pygame\Nado Game\pyqt5\자재관리\입고대장.xlsx'):
    LE =  [
        'E:/source/pygame/Nado Game/pyqt5/자재관리/입고대장.xlsx',
        'E:/source/pygame/Nado Game/pyqt5/자재관리/사용대장.xlsx',
        'E:/source/pygame/Nado Game/pyqt5/자재관리/동호대장.xlsx',
        ]
else: 
    LE =  [
        'C:/source/pygame/Nado Game/pyqt5/자재관리/입고대장.xlsx',
        'C:/source/pygame/Nado Game/pyqt5/자재관리/사용대장.xlsx',
        'C:/source/pygame/Nado Game/pyqt5/자재관리/동호대장.xlsx',
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
        self.dateEdit.setDate(QDate.currentDate())
        self.dateEdit.setCalendarPopup(True)
        self.init_in_data_make()
        self.init_out_data_make()
        self.init_onstock_query()
        
        #self.dateEdit.selectionChanged.connect(self.set_calendar_today_color)
        self.comboBox.activated.connect(self.onstock_query_combo_spec)#입고품목 선택시 품목 규격 콤보박스 항목 선택
        self.comboBox_5.activated.connect(self.comboBox_5Activated)#입고품목 선택시 품목 규격 콤보박스 항목 선택
        self.comboBox_9.activated.connect(self.comboBox_9Activated)#사용 품목규격 선택시 품목 재고 보임
        self.comboBox_5.activated.connect(self.in_stock_view)#입고 품목 선택시 품목 재고 보임
        self.comboBox_7.activated.connect(self.out_stock_view)#사용 품목규격 선택시 품목 재고 보임
        self.comboBox_6.activated.connect(self.in_stock_view)#입고 품목규격 선택시 품목 재고 보임
        self.comboBox_9.activated.connect(self.out_stock_view)#사용 품목 선택시 품목 재고 보임
        self.comboBox_10.activated.connect(self.out_dongho)#동 선택시 호수 콤보 선택

        self.pushButton.clicked.connect(self.addComboBoxItem)# 신규 품목 추가
        self.pushButton_2.clicked.connect(self.addComboBoxSpecItem) #신규 항목 추가
        self.pushButton_7.clicked.connect(self.inTableToSaveExcelFile)
        self.pushButton_9.clicked.connect(self.outTableToSaveExcelFile)
        self.pushButton_6.clicked.connect(self.addInMaterialToTable)
        self.pushButton_12.clicked.connect(self.onstock_view)
        self.pushButton_11.clicked.connect(self.addOutMaterialToTable)
        self.lineEdit.textChanged.connect(self.lineEditChanged)
        self.lineEdit_2.textChanged.connect(self.lineEdit_2Changed)


    def set_calendar_today_color(self):
        #today = QDate.currentDate()
        self.dateEdit.showToday()
        #pass
    def init_onstock_query(self):
        self.onstock_query_combo_items_spec()
        df = self.on_stock()
        df_list = df.values.tolist()
        for list in df_list:
            self.set_tbl_onstock(list)

    def onstock_view(self):
        colcount = self.tableWidget.columnCount()
        headers = [self.tableWidget.horizontalHeaderItem(x).text() for x in range(0,colcount)]
        self.tableWidget.clear()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setHorizontalHeaderLabels(headers)
        df_sel = self.df_onstock_selection()
        df_list = df_sel.values.tolist()
        for l in df_list:
            self.set_tbl_onstock(l)
        self.table_display()

    def onstock_selection_in(self, df):
        date = self.dateEdit.text()
        items = self.comboBox.currentText()
        spec = self.comboBox_4.currentText()
        d_con = df['입고일'] <=date
        i_con = df['품명'] == items
        s_con = df['규격'] == spec
        if items == 'All':
            df_sel = df[(d_con)]
            return df_sel
        else:
            df_sel = df[(d_con & i_con & s_con)]
            return df_sel

    def onstock_selection_out(self, df):
        date = self.dateEdit.text()
        items = self.comboBox.currentText()
        spec = self.comboBox_4.currentText()
        d_con = df['사용일'] <=date
        i_con = df['품명'] == items
        s_con = df['규격'] == spec
        if items == 'All':
            df_sel = df[(d_con)]
            return df_sel
        else:
            df_sel = df[(d_con & i_con & s_con)]
            return df_sel

    def df_onstock_selection(self):
        dfI = self.in_df()
        dfIn = self.onstock_selection_in(dfI)
        df_in = dfIn[['품명','규격', '입고수량']].copy()
        df_in_sum = df_in.groupby(['품명','규격']).sum()

        dfO = self.out_df()
        dfOut = self.onstock_selection_out(dfO)
        df_out = dfOut[['품명','규격', '사용수량']].copy()
        df_out_sum = df_out.groupby(['품명','규격']).sum()

        df_on_stock = pd.merge(df_in_sum, df_out_sum, how = 'outer', on = ['품명','규격'])
        df_on_stock.fillna(0, inplace=True)
        try:
            df_on_stock['재고'] = df_on_stock['입고수량'] - df_on_stock['사용수량']
            df_on_stock[['입고수량', '사용수량','재고']] = df_on_stock[['입고수량', '사용수량','재고']].astype('str')
            df_m = df_on_stock.reset_index().copy()
            return df_m
        except:
            pass
                    
    def set_tbl_onstock(self,df_list):
        rowCount = self.tableWidget.rowCount()
        self.tableWidget.setRowCount(rowCount+1)
        self.tableWidget.setColumnCount(len(df_list)+1)
        c = 0
        for i in df_list:
            self.tableWidget.setItem(rowCount, c, QTableWidgetItem(i))
            c = c+1

    def on_stock(self):
        dfIn = self.in_df()
        df_in = dfIn[['품명','규격', '입고수량']].copy()
        df_in_sum = df_in.groupby(['품명','규격']).sum()

        dfOut = self.out_df()
        df_out = dfOut[['품명','규격', '사용수량']].copy()
        df_out_sum = df_out.groupby(['품명','규격']).sum()

        df_on_stock = pd.merge(df_in_sum, df_out_sum, how = 'outer', on = ['품명','규격'])
        df_on_stock.fillna(0, inplace=True)
        try:
            df_on_stock['재고'] = df_on_stock['입고수량'] - df_on_stock['사용수량']
            df_on_stock[['입고수량', '사용수량','재고']] = df_on_stock[['입고수량', '사용수량','재고']].astype('str')
            df_m = df_on_stock.reset_index().copy()
            return df_m
        except:
            pass

    def onstock_query_combo_spec(self):    
        df = self.in_df_make()
        if self.comboBox.currentText() == 'All':
            self.comboBox_4.clear()
            self.comboBox_4.addItems(['All'])
        else:
            df = df[(df['품명'] == self.comboBox.currentText())]
            spec = df['규격'].unique()
            spec.sort()
            self.comboBox_4.clear()
            self.comboBox_4.addItems(spec)

    def onstock_query_combo_items_spec(self):    
        df = self.in_df_make()
        items = df['품명'].unique()
        items.sort()
        items = np.insert(items, 0,'All')
        #items = items.insert(0,'All')
        self.comboBox.clear()
        self.comboBox.addItems(items)    
        if self.comboBox.currentText() == 'All':
            self.comboBox_4.addItems(['All'])
            
        else:
            df = df[(df['품명'] == self.comboBox.currentText())]
            spec = df['규격'].unique()
            spec.sort()
            self.comboBox_4.addItems(spec)
        return df

    def init_out_data_make(self):
        df = self.out_df()
        self.out_file_to_table(df)
        self.out_dongho()
        self.comboBox_8.clear()
        self.comboBox_8.addItems(['공용','세대'])
        self.out_combo_items_spec()
        
    def outTableToSaveExcelFile(self):
        file = LE[1] #r'C:\source\pygame\Nado Game\pyqt5\자재관리\사용대장.xlsx'
        df = self.out_data_query()
        if os.path.isfile(file):
            os.remove(file)
            df.to_excel(file,index=False,header=True)
        else:
            df.to_excel(file,index=False,header=True)
        return 

    def out_data_query(self):
        '''
        data query from tablewidget to pandas dataframe
        '''
        rowcount = self.tableWidget_6.rowCount()
        colcount = self.tableWidget_6.columnCount()
        
        headers = [self.tableWidget_6.horizontalHeaderItem(x).text() for x in range(0,colcount)]
        data_list = []
        for i in range(0, rowcount):
            data =[]
            for j in range(0, colcount):
                d = self.tableWidget_6.item(i,j).text()
                data.append(d)
            data_list.append(data)
        df = pd.DataFrame(data_list) # list to dataframe
        df.columns = headers # set the hwaders on dataframe
        
        return df

    def out_combo_items_spec(self):    
        df = self.in_df_make()
        items = df['품명'].unique()
        items.sort()
        self.comboBox_9.clear()
        self.comboBox_9.addItems(items)    
        df = df[(df['품명'] == self.comboBox_9.currentText())]
        spec = df['규격'].unique()
        spec.sort()
        self.comboBox_7.addItems(spec)
        return df
        
    def addOutMaterialToTable(self):
        
        data = []
        data.append(self.dateEdit_6.text())
        data.append(self.comboBox_10.currentText())
        data.append(self.comboBox_11.currentText())
        data.append(self.comboBox_8.currentText())
        data.append(self.comboBox_9.currentText())
        data.append(self.comboBox_7.currentText())
        if len(self.lineEdit_9.text()) != 0:    
            data.append(self.lineEdit_9.text())
        else:
            QMessageBox.about(self, "경고", "수량 자료를 입력하세요")
            return

        if len(self.lineEdit_6.text())==0:
            data.append('**')
        else:
            data.append(self.lineEdit_6.text())

        self.set_tbl_6(data)
        self. outTableToSaveExcelFile()

    def out_stock_view(self):
        #self.comboBox_9Activated()
        list = [self.comboBox_9.currentText(), self.comboBox_7.currentText()]
        on_stock_qty = self.items_spec_onstock(list[0], list[1])
        self.lineEdit_10.setText(on_stock_qty)

    def in_stock_view(self):
        list = [self.comboBox_5.currentText(), self.comboBox_6.currentText()]
        on_stock_qty = self.items_spec_onstock(list[0], list[1])
        self.lineEdit_11.setText(on_stock_qty)

    def items_spec_onstock(self, items, spec):
        df_on_stock = self.on_stock()
        try:
            on_stock_qty = df_on_stock.loc[[(items, spec)]].values.tolist()
            return str(on_stock_qty[0][2])
        except:
            on_stock_qty = '신규항목임'
            return on_stock_qty
    
    def set_tbl_6(self,data):
        rowCount = self.tableWidget_6.rowCount()
        self.tableWidget_6.setRowCount(rowCount+1)
        self.tableWidget_6.setColumnCount(len(data))
        c = 0
        for i in data:
            self.tableWidget_6.setItem(rowCount, c, QTableWidgetItem(i))
            c = c+1
        self.table_display()

    def out_file_to_table(self, df):
        df[['동', '호','사용수량']] = df[['동', '호','사용수량']].astype('str')
        df.fillna(' ')
        list = df.values.tolist()

        for d in list:
            self.set_tbl_6(d)
        self.tableWidget_5.scrollToBottom
        self.table_display()
    
    def out_df(self):
        file = LE[1] #r'C:\source\pygame\Nado Game\pyqt5\자재관리\사용대장.xlsx'
        with pd.ExcelFile(file) as f:
            df = pd.read_excel(f,skiprows=0)
        return df

    def in_df(self):
        file = LE[0] #r'C:\source\pygame\Nado Game\pyqt5\자재관리\입고대장.xlsx'
        with pd.ExcelFile(file) as f:
            df = pd.read_excel(f,skiprows=0)
        return df


    def dong_ho(self):
        file = LE[2] #r'C:\source\pygame\Nado Game\pyqt5\자재관리\동호대장.xlsx'
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
        items.sort()
        self.comboBox_9.clear()
        self.comboBox_9.addItems(items)
        df1 = df[(df['품명'] == self.comboBox_9.currentText())]
        spec = df1['규격'].unique()
        spec.sort()
        self.comboBox_7.clear()
        self.comboBox_7.addItems(spec)

    def comboBox_9Activated(self):
        df = self.in_df_make()
        items = df['품명'].unique()
        items.sort()
        df1 = df[(df['품명'] == self.comboBox_9.currentText())]
        spec = df1['규격'].unique()
        spec.sort()
        self.comboBox_7.clear()
        self.comboBox_7.addItems(spec)

    def out_df_make(self):
        file = LE[1] #r'C:\source\pygame\Nado Game\pyqt5\자재관리\사용대장.xlsx'
        with pd.ExcelFile(file) as f:
            df = pd.read_excel(f,skiprows=0)
        return df

    def in_df_make(self):
        file = LE[0] #r'C:\source\pygame\Nado Game\pyqt5\자재관리\입고대장.xlsx'
        with pd.ExcelFile(file) as f:
            df = pd.read_excel(f,skiprows=0)
        return df
    
    def comboBox_5Activated(self):
        df = self.in_df_make()
        df = df[(df['품명'] == self.comboBox_5.currentText())]
        items = df['품명'].unique()
        items.sort()
        spec = df['규격'].unique()
        spec.sort()
        self.comboBox_6.clear()
        self.comboBox_6.addItems(spec)

    def init_in_data_make(self):
        self.in_combo_items_spec()
        df = self.in_df_make()
        headers = df.columns.values.tolist()
        df[['입고수량', '구입금액','단가']] = df[['입고수량', '구입금액','단가']].astype('str')
        df.fillna(' ')
        list = df.values.tolist()
        self.tableWidget_5.setHorizontalHeaderLabels(headers)
        #self.tableWidget_5.horizontalHeaderItem().setSectionResizeMode(QHeaderView.Stretch)
        for d in list:
            self.set_tbl(d)
        self.table_display()
        self.tableWidget_5.scrollToBottom

    def in_combo_items_spec(self):
        df = self.in_df_make()
        items = df['품명'].unique()
        items.sort()
        self.comboBox_5.clear()
        self.comboBox_5.addItems(items)    
        df = df[(df['품명'] == self.comboBox_5.currentText())]
        spec = df['규격'].unique()
        spec.sort()
        self.comboBox_6.addItems(spec)

    def inTableToSaveExcelFile(self):
        file = LE[0]#r'C:\source\pygame\Nado Game\pyqt5\자재관리\입고대장.xlsx'
        df = self.data_query()
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
        data_list = []
        for i in range(0, rowcount):
            data =[]
            for j in range(0, colcount):
                d = self.tableWidget_5.item(i,j).text()
                data.append(d)
            data_list.append(data)
        df = pd.DataFrame(data_list) # list to dataframe
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
        self.lineEdit_5.setText('')
    
    def addComboBoxSpecItem(self) :
        self.comboBox_6.addItem(self.lineEdit_8.text())
        self.lineEdit_8.setText('')
    
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
            in_data.append('*')
        else:
            in_data.append(self.lineEdit_4.text())
        if len(self.lineEdit_6.text())==0:
            in_data.append('*')
        else:
            in_data.append(self.lineEdit_6.text())

        self.set_tbl(in_data)
        self.inTableToSaveExcelFile()
    
    def set_tbl(self,data):
        rowCount = self.tableWidget_5.rowCount()
        self.tableWidget_5.setRowCount(rowCount+1)
        self.tableWidget_5.setColumnCount(len(data))
        c = 0
        for i in data:
            self.tableWidget_5.setItem(rowCount, c, QTableWidgetItem(i))
            c = c+1
        
        self.table_display()

    def table_display(self):
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    elWindow = ElWindow()
    elWindow.show()
    app.exec_()