import sys
import os
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal,QDate, QTime, Qt
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
HEADERS = [
    ['일자', '품명', '규격', '입고수량', '구입금액', '단가', '구입업체', '비고'],
    ['일자', '동', '호', '공용', '품명' ,'규격','사용수량','비고'],
    ['품명','규격','입고수량','사용수량','재고수량','비고'],
    ['구분','일자', '품명', '규격', '입고수량','입고누계', '구입금액', '단가', '구입업체', '비고'],
    ['구분','일자', '동', '호', '공용', '품명' ,'규격','사용수량','사용누계','비고'],
    ['구분','일자', '품명', '규격', '입고수량','입고누계','동', '호', '공용','사용수량','사용누계', '재고수량']
]


class MatWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.LE = LE
        self.setupUi(self)

        # 자재입고 입력 init setup
        now = QDate.currentDate()
        now.toString(Qt.ISODate)
        today = now.addMonths(-3)
        self.DE_inUsedQueryFromDate.setDate(today)
        self.DE_inUsedQueryFromDate.setCalendarPopup(True)
        self.DE_inUsedQueryToDate.setDate(QDate.currentDate())
        self.DE_inUsedQueryToDate.setCalendarPopup(True)
        self.inDate.setDate(QDate.currentDate())
        self.inDate.setCalendarPopup(True)
        self.outDate.setDate(QDate.currentDate())
        self.outDate.setCalendarPopup(True)
        self.DE_detailedQueryFromDate.setDate(today)
        self.DE_detailedQueryFromDate.setCalendarPopup(True)
        self.DE_detailedQueryToDate.setDate(QDate.currentDate())
        self.DE_detailedQueryToDate.setCalendarPopup(True)
        self.onstockDate.setDate(QDate.currentDate())
        self.onstockDate.setCalendarPopup(True)
        self.init_in_data_input()
        self.init_out_data_input()
        self.init_onstock_query()
        self.init_in_query()
        self.init_detailed_total_query()

        
        #self.onstockDate.selectionChanged.connect(self.set_calendar_today_color)
        self.CB_onstockItems.activated.connect(self.onstock_query_combo_spec)#입고품목 선택시 품목 규격 콤보박스 항목 선택
        self.CB_inUsedQueryItems.activated.connect(self.in_query_combo_spec)#입고품목 선택시 품목 규격 콤보박스 항목 선택
        self.CB_detailedQueryItems.activated.connect(self.in_out_query_combo_spec)#입고품목 선택시 품목 규격 콤보박스 항목 선택
        #self.CB_detailedQuerySpecs.activated.connect(self.detailed_total_query)#입고품목 선택시 품목 규격 콤보박스 항목 선택
        self.comboInItems.activated.connect(self.comboInItemsActivated)#입고품목 선택시 품목 규격 콤보박스 항목 선택
        self.CB_outItems.activated.connect(self.comboBox_9Activated)#사용 품목규격 선택시 품목 재고 보임
        self.comboInItems.activated.connect(self.in_stock_view)#입고 품목 선택시 품목 재고 보임
        self.CB_outSpecs.activated.connect(self.out_stock_view)#사용 품목규격 선택시 품목 재고 보임
        self.comboInSpecs.activated.connect(self.in_stock_view)#입고 품목규격 선택시 품목 재고 보임
        self.CB_outItems.activated.connect(self.out_stock_view)#사용 품목 선택시 품목 재고 보임
        self.CB_outDong.activated.connect(self.out_dongho)#동 선택시 호수 콤보 선택

        self.PB_inAddNewItem.clicked.connect(self.addComboBoxItem)# 신규 품목 추가
        self.pushButton_2.clicked.connect(self.addComboBoxSpecItem) #신규 항목 추가
        self.PB_InAdd.clicked.connect(self.addInMaterialToTable)
        self.PB_InSave.clicked.connect(self.inTableToSaveExcelFile)
        self.PB_InExit.clicked.connect(self.close)

        self.pushButton_9.clicked.connect(self.outTableToSaveExcelFile)
        self.PB_onstockQuery.clicked.connect(self.onstock_view)# 자재 품목/규격 별 제고 조회
        self.PB_inUsedQuery.clicked.connect(self.in_status_view) # 품목/규격 별 자대 입고 현황 조회 
        self.PB_detailedQuery.clicked.connect(self.detailed_total_query) # 품목/규격 별 자대 입고 현황 조회 
        self.pushButton_11.clicked.connect(self.addOutMaterialToTable)
        self.LE_InQty.textChanged.connect(self.lineEditChanged)
        self.LE_InPrice.textChanged.connect(self.lineEdit_2Changed)


    def init_detailed_total_query(self):
        self.in_out_query_combo_items_spec()
        df_list = self.detailed_in_out_list()
        df_in_out = self.detailed_in_out_df(df_list)
        headers = df_in_out.columns.values.tolist()
        df_in_out_values_list = df_in_out.values.tolist()

        self.detailedQueryTableWidget.setHorizontalHeaderLabels(headers)
        for i in df_in_out_values_list:
            self.set_tbl_3(i)
        self.table_display_3()

    def detailed_total_query(self):
        #self.in_out_query_combo_items_spec()
        df_list = self.detailed_in_out_list()
        df_in_out = self.detailed_in_out_df(df_list)
        if len(df_in_out) == 0:
            QMessageBox.about(self, "경고", "검색 기간 동안에 해당 품목에 대한 입출고 기록이 없습니다")
            return
        headers = df_in_out.columns.values.tolist()
        df_in_out_values_list = df_in_out.values.tolist()
        self.detailedQueryTableWidget.clear()
        self.detailedQueryTableWidget.setRowCount(0)
        self.detailedQueryTableWidget.setHorizontalHeaderLabels(headers)
        for i in df_in_out_values_list:
            self.set_tbl_3(i)
        self.table_display_3()
        

    def set_tbl_3(self, df_list):
        rowCount = self.detailedQueryTableWidget.rowCount()
        self.detailedQueryTableWidget.setRowCount(rowCount+1)
        self.detailedQueryTableWidget.setColumnCount(len(df_list))
        c = 0
        for i in df_list:
            self.detailedQueryTableWidget.setItem(rowCount, c, QTableWidgetItem(i))
            c = c+1
    
    def table_display_3(self):
        header = self.detailedQueryTableWidget.horizontalHeader()
        twidth = header.width()
        width = []
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            width.append(header.sectionSize(column))
        
        wfactor = int(twidth / sum(width))
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            header.resizeSection(column, width[column]*wfactor)
        self.detailedQueryTableWidget.scrollToBottom

    def df_status_selection(self, df):
        from_date = self.DE_detailedQueryFromDate.text()
        to_date = self.DE_detailedQueryToDate.text()
        
        items = self.CB_detailedQueryItems.currentText()
        spec = self.CB_detailedQuerySpecs.currentText()
        date_to_con = df['일자'] <= to_date
        date_from_con = df['일자'] >= from_date
        i_con = df['품명'] == items
        s_con = df['규격'] == spec
        if items == 'All':
            df_sel = df[(date_from_con & date_to_con)]
            return df_sel
        else:
            df_sel = df[(date_from_con & date_to_con & i_con & s_con)]
            return df_sel

    def detailed_in_out_list(self):
        dfI = self.in_df()
        dfI['입출'] ='입고'
        dfIn = self.df_status_selection(dfI)
        dfO = self.out_df()
        dfO['입출'] = '사용'
        dfOut = self.df_status_selection(dfO)
        items_in = set(dfIn['품명'].unique())
        specs_in = set(dfIn['규격'].unique())
        items_out = set(dfOut['품명'].unique())
        specs_out = set(dfOut['규격'].unique())
        items = list(items_in.union(items_out))
        specs = list(specs_in.union(specs_out))
        temp_list = []
        for item in items:
            for spec in specs:
                dfIn_sel = dfIn[((dfIn['품명'] == item) & (dfIn['규격'] == spec))]
                dfOut_sel = dfOut[((dfOut['품명'] == item) & (dfOut['규격'] ==  spec))]
                df_on_stock = pd.merge(dfIn_sel, dfOut_sel, how = 'outer', on = ['입출','일자','품명','규격'])
                df_on_stock.fillna(0, inplace=True)
                df_on_stock.sort_values(by= '일자', inplace=True)
                df_total = df_on_stock[['일자','품명','규격','입출','입고수량','구입금액','단가','동','호','사용수량']]
                df_total.reset_index(drop=True, inplace=True)
                df_total['sum'] = df_total['입고수량'] - df_total['사용수량']
                df_temp = df_total[['sum']].copy()
                df_temp_1  = df_temp.cumsum()
                df_total['sum'] = df_temp_1['sum']
                df_total[['입고수량','구입금액','단가','동','사용수량','sum']].astype('int')
                if df_total.empty:
                    pass
                else:
                    temp_list.append(df_total)
        return temp_list

    def detailed_in_out_df(self, df_list):
        if len(df_list) == 0:
            return df_list
        df_con = df_list[0]
        for part in df_list[1:]:
            df_con = pd.concat([df_con, part])
            df_con.reset_index(drop=True, inplace=True)
        df_con[['입고수량','구입금액','단가','동','사용수량','sum']]= df_con[['입고수량','구입금액','단가','동','사용수량','sum']].astype('int')
        df_con[['입고수량','구입금액','단가','동','호','사용수량','sum']] = df_con[['입고수량','구입금액','단가','동','호','사용수량','sum']].astype('str')
        return df_con




    def init_in_query(self):
        self.in_query_combo_items_spec()
        df = self.in_df()
        df_in = self.in_out_status(df)
        df_list = df_in.values.tolist()
        for list in df_list:
            self.set_inUsedTableWidge(list)
        self.table_display_status()
    
    def init_out_query(self):
        self.in_out_query_combo_items_spec()
        df = self.out_df()
        df_in = self.in_out_status(df)
        df_list = df_in.values.tolist()
        for list in df_list:
            self.set_tbl_3(list)
        #pass
    

    def in_status_view(self):
        if self.CB_inUsedInOut.currentText() == '입고':
            colcount = self.inUsedTableWidget.columnCount()
            headers = [self.inUsedTableWidget.horizontalHeaderItem(x).text() for x in range(0,colcount)]
            self.inUsedTableWidget.clear()
            self.inUsedTableWidget.setRowCount(0)
            self.inUsedTableWidget.setHorizontalHeaderLabels(headers)
            df_sel = self.df_in_status_selection()
            df_list = df_sel.values.tolist()
            for l in df_list:
                self.set_inUsedTableWidge(l)
            self.table_display_status()
        else:
            colcount = 8
            headers = []
            self.inUsedTableWidget.clear()
            self.inUsedTableWidget.setRowCount(0)
            self.inUsedTableWidget.setHorizontalHeaderLabels(headers)

    def table_display_status(self):
        header = self.inUsedTableWidget.horizontalHeader()
        twidth = header.width()
        width = []
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            width.append(header.sectionSize(column))
        
        wfactor = int(twidth / sum(width))
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            header.resizeSection(column, width[column]*wfactor)
        self.inUsedTableWidget.scrollToBottom



    def df_in_status_selection(self):
        dfI = self.in_df()
        dfIn = self.in_status_selection(dfI)
        
        df_in = dfIn[['품명','규격', '입고수량']].copy()
        df_in_sum = df_in.groupby(['품명','규격']).sum()

        dfO = self.out_df()
        dfOut = self.out_status_selection(dfO)
        
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

    def in_status_selection(self, df):
        from_date = self.DE_inUsedQueryFromDate.text()
        to_date = self.DE_inUsedQueryToDate.text()
        items = self.CB_inUsedQueryItems.currentText()
        spec = self.CB_inUsedQuerySpecs.currentText()
        date_to_con = df['일자'] <= to_date
        date_from_con = df['일자'] >= from_date
        i_con = df['품명'] == items
        s_con = df['규격'] == spec
        if items == 'All':
            df_sel = df[(date_from_con & date_to_con)]
            return df_sel
        else:
            df_sel = df[(date_from_con & date_to_con & i_con & s_con)]
            return df_sel

    def df_out_status_selection(self):
        dfI = self.in_df()
        dfIn = self.in_status_selection(dfI)
        
        df_in = dfIn[['품명','규격', '입고수량']].copy()
        df_in_sum = df_in.groupby(['품명','규격']).sum()

        dfO = self.out_df()
        dfOut = self.out_status_selection(dfO)
        
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

    def out_status_selection(self, df):
        from_date = self.DE_inUsedQueryFromDate.text()
        to_date = self.DE_inUsedQueryToDate.text()
        items = self.CB_inUsedQueryItems.currentText()
        spec = self.CB_inUsedQuerySpecs.currentText()
        d_to_con = df['일자'] <=to_date
        d_from_con = df['일자'] >=from_date
        i_con = df['품명'] == items
        s_con = df['규격'] == spec
        if items == 'All':
            df_sel = df[(d_to_con & d_from_con)]
            return df_sel
        else:
            df_sel = df[(d_to_con & d_from_con & i_con & s_con)]
            return df_sel



    def in_out_query_combo_items_spec(self):    
        df = self.in_df()
        items = df['품명'].unique()
        items.sort()
        items = np.insert(items, 0,'All')
        self.CB_detailedQueryItems.clear()
        self.CB_detailedQueryItems.addItems(items)    
        if self.CB_detailedQueryItems.currentText() == 'All':
            self.CB_detailedQuerySpecs.addItems(['All'])
            
        else:
            df = df[(df['품명'] == self.CB_detailedQueryItems.currentText())]
            spec = df['규격'].unique()
            spec.sort()
            self.CB_detailedQuerySpecs.addItems(spec)

    def set_inUsedTableWidge(self, df_list):
        rowCount = self.inUsedTableWidget.rowCount()
        self.inUsedTableWidget.setRowCount(rowCount+1)
        self.inUsedTableWidget.setColumnCount(len(df_list))
        c = 0
        for i in df_list:
            self.inUsedTableWidget.setItem(rowCount, c, QTableWidgetItem(i))
            c = c+1

    def in_out_query_combo_spec(self):
        
        df = self.in_df()
        if self.CB_detailedQueryItems.currentText() == 'All':
            self.CB_detailedQuerySpecs.clear()
            self.CB_detailedQuerySpecs.addItems(['All'])
        else:
            df = df[(df['품명'] == self.CB_detailedQueryItems.currentText())]
            spec = df['규격'].unique()
            spec.sort()
            self.CB_detailedQuerySpecs.clear()
            self.CB_detailedQuerySpecs.addItems(spec)

    def in_out_status(self, df):
        items = df['품명'].unique()
        df_lists = []
        for item in items:
            df_specs = df[(df['품명'] == item)]
            specs = df_specs['규격'].unique()
            for spec in specs:
                df_sel = df[(df['품명'] == item) & (df['규격'] == spec)].copy()
                try:
                    df_temp = df_sel.sort_values(by=['일자']).copy()
                    df_copy = df_temp[['입고수량']].copy()
                except:
                    df_temp = df_sel.sort_values(by=['일자']).copy()
                    df_copy = df_temp[['사용수량']].copy()
                df_copy['품목누계'] = df_copy.cumsum()
                df_temp['품목누계']=df_copy['품목누계']
                df_lists.append(df_temp)
        df_con = df_lists[0]
        for df_list in df_lists[1:]:
            df_con = pd.concat([df_con, df_list])
        #df_con.columns.tolist()
        try:
            df_con_1= df_con[['일자', '품명', '규격', '입고수량', '품목누계', '구입금액', '단가', '구입업체', '비고' ]]
            df_con_1.sort_values(by=['일자', '품명','규격'], inplace=True)
            df_con_1[['입고수량', '구입금액','단가','품목누계']] = df_con[['입고수량', '구입금액','단가','품목누계']].astype('str')
        except:
            df_con_1 = df_con[['일자', '동','호','구분','품명', '규격', '사용수량', '품목누계', '비고' ]]
            
            df_con_1.sort_values(by=['일자', '품명','규격'])
            df_con_1[['사용수량', '동','호','품목누계']] = df_con[['사용수량', '동','호','품목누계']].astype('str')

        return df_con_1


    def in_query_combo_items_spec(self):    
        df = self.in_df()
        items = df['품명'].unique()
        items.sort()
        items = np.insert(items, 0,'All')
        self.CB_inUsedQueryItems.clear()
        self.CB_inUsedQueryItems.addItems(items)    
        if self.CB_inUsedQueryItems.currentText() == 'All':
            self.CB_inUsedQuerySpecs.addItems(['All'])
            
        else:
            df = df[(df['품명'] == self.CB_onstockItems.currentText())]
            spec = df['규격'].unique()
            spec.sort()
            self.CB_inUsedQuerySpecs.addItems(spec)
        return df

    def in_query_combo_spec(self):
        
        df = self.in_df()
        if self.CB_inUsedQueryItems.currentText() == 'All':
            self.CB_inUsedQuerySpecs.clear()
            self.CB_inUsedQuerySpecs.addItems(['All'])
        else:
            df = df[(df['품명'] == self.CB_inUsedQueryItems.currentText())]
            spec = df['규격'].unique()
            spec.sort()
            self.CB_inUsedQuerySpecs.clear()
            self.CB_inUsedQuerySpecs.addItems(spec)

    def set_calendar_today_color(self):
        #today = QDate.currentDate()
        self.onstockDate.showToday()
        #pass

    def init_onstock_query(self):
        self.onstock_query_combo_items_spec()
        df = self.on_stock()
        df_list = df.values.tolist()
        for list in df_list:
            self.set_onstockTableWidget(list)
        self.table_display_onstock()

    def table_display_onstock(self):
        header = self.onstockTableWidget.horizontalHeader()
        twidth = header.width()
        width = []
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            width.append(header.sectionSize(column))
        
        wfactor = int(twidth / sum(width))
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            header.resizeSection(column, width[column]*wfactor)
        self.onstockTableWidget.scrollToBottom


    def onstock_view(self):
        colcount = self.onstockTableWidget.columnCount()
        headers = [self.onstockTableWidget.horizontalHeaderItem(x).text() for x in range(0,colcount)]
        self.onstockTableWidget.clear()
        self.onstockTableWidget.setRowCount(0)
        self.onstockTableWidget.setHorizontalHeaderLabels(headers)
        df_sel = self.df_onstock_selection()
        df_list = df_sel.values.tolist()
        for l in df_list:
            self.set_onstockTableWidget(l)
        self.table_display_onstock()

    def onstock_selection_in(self, df):
        date = self.onstockDate.text()
        items = self.CB_onstockItems.currentText()
        spec = self.CB_onstockSpecs.currentText()
        d_con = df['일자'] <=date
        i_con = df['품명'] == items
        s_con = df['규격'] == spec
        if items == 'All':
            df_sel = df[(d_con)]
            return df_sel
        else:
            df_sel = df[(d_con & i_con & s_con)]
            return df_sel

    def onstock_selection_out(self, df):
        date = self.onstockDate.text()
        items = self.CB_onstockItems.currentText()
        spec = self.CB_onstockSpecs.currentText()
        d_con = df['일자'] <=date
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
                    
    def set_onstockTableWidget(self,df_list):
        rowCount = self.onstockTableWidget.rowCount()
        self.onstockTableWidget.setRowCount(rowCount+1)
        self.onstockTableWidget.setColumnCount(len(df_list)+1)
        c = 0
        for i in df_list:
            self.onstockTableWidget.setItem(rowCount, c, QTableWidgetItem(i))
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
        df = self.in_df()
        if self.CB_onstockItems.currentText() == 'All':
            self.CB_onstockSpecs.clear()
            self.CB_onstockSpecs.addItems(['All'])
        else:
            df = df[(df['품명'] == self.CB_onstockItems.currentText())]
            spec = df['규격'].unique()
            spec.sort()
            self.CB_onstockSpecs.clear()
            self.CB_onstockSpecs.addItems(spec)

    def onstock_query_combo_items_spec(self):    
        df = self.in_df()
        items = df['품명'].unique()
        items.sort()
        items = np.insert(items, 0,'All')
        #items = items.insert(0,'All')
        self.CB_onstockItems.clear()
        self.CB_onstockItems.addItems(items)    
        if self.CB_onstockItems.currentText() == 'All':
            self.CB_onstockSpecs.addItems(['All'])
            
        else:
            df = df[(df['품명'] == self.CB_onstockItems.currentText())]
            spec = df['규격'].unique()
            spec.sort()
            self.CB_onstockSpecs.addItems(spec)
        return df

    def init_out_data_input(self):
        df = self.out_df()
        self.out_file_to_table(df)
        self.out_dongho()
        self.CB_outGongSe.clear()
        self.CB_outGongSe.addItems(['공용','세대'])
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
        rowcount = self.usedIntableWidget.rowCount()
        colcount = self.usedIntableWidget.columnCount()
        
        headers = [self.usedIntableWidget.horizontalHeaderItem(x).text() for x in range(0,colcount)]
        data_list = []
        for i in range(0, rowcount):
            data =[]
            for j in range(0, colcount):
                d = self.usedIntableWidget.item(i,j).text()
                data.append(d)
            data_list.append(data)
        df = pd.DataFrame(data_list) # list to dataframe
        df.columns = headers # set the hwaders on dataframe
        
        return df

    def out_combo_items_spec(self):    
        df = self.in_df()
        items = df['품명'].unique()
        items.sort()
        self.CB_outItems.clear()
        self.CB_outItems.addItems(items)    
        df = df[(df['품명'] == self.CB_outItems.currentText())]
        spec = df['규격'].unique()
        spec.sort()
        self.CB_outSpecs.addItems(spec)
        return df
        
    def addOutMaterialToTable(self):
        
        data = []
        data.append(self.outDate.text())
        data.append(self.CB_outDong.currentText())
        data.append(self.CB_outHo.currentText())
        data.append(self.CB_outGongSe.currentText())
        data.append(self.CB_outItems.currentText())
        data.append(self.CB_outSpecs.currentText())
        if len(self.LE_outUsedQty.text()) != 0:    
            data.append(self.LE_outUsedQty.text())
        else:
            QMessageBox.about(self, "경고", "수량 자료를 입력하세요")
            return

        if len(self.LE_outRemarks.text())==0:
            data.append('**')
        else:
            data.append(self.LE_outRemarks.text())

        self.set_usedIntableWidget(data)

        self. outTableToSaveExcelFile()

    def out_stock_view(self):
        #self.comboBox_9Activated()
        list = [self.CB_outItems.currentText(), self.CB_outSpecs.currentText()]
        on_stock_qty = self.items_spec_onstock(list[0], list[1])
        self.LE_outOnstock.setText(on_stock_qty)

    def in_stock_view(self):
        list = [self.comboInItems.currentText(), self.comboInSpecs.currentText()]
        on_stock_qty = self.items_spec_onstock(list[0], list[1])
        self.LE_InOnStosckQty.setText(on_stock_qty)

    def items_spec_onstock(self, items, spec):
        df_on_stock = self.on_stock()
        df_on_stock.set_index(['품명', '규격'], inplace=True)
        try:
            on_stock_qty = df_on_stock.loc[[(items, spec)],'재고'].values.tolist()
            on_stock_qty = on_stock_qty[0]
            return on_stock_qty
        except:
            on_stock_qty = '신규항목임'
            return on_stock_qty
    
    def set_usedIntableWidget(self,data):
        rowCount = self.usedIntableWidget.rowCount()
        self.usedIntableWidget.setRowCount(rowCount+1)
        self.usedIntableWidget.setColumnCount(len(data))
        c = 0
        for i in data:
            self.usedIntableWidget.setItem(rowCount, c, QTableWidgetItem(i))
            c = c+1
        #self.table_display()






    def out_file_to_table(self, df):
        df[['동','사용수량']] = df[['동','사용수량']].astype('int')
        df[['동', '호','사용수량']] = df[['동', '호','사용수량']].astype('str')
        df.fillna(' ')
        list = df.values.tolist()

        for d in list:
            self.set_usedIntableWidget(d)
        self.tableWidgetInIn.scrollToBottom

    def dong_ho(self):
        file = LE[2] #r'C:\source\pygame\Nado Game\pyqt5\자재관리\동호대장.xlsx'
        with pd.ExcelFile(file) as f:
            df = pd.read_excel(f,skiprows=0)
            df[['동','호']] = df[['동','호']].astype('str')
        return df

    def out_dongho(self):
        df = self.dong_ho()
        dong = df['동'].unique()
        self.CB_outHo.clear()
        self.CB_outDong.addItems(dong)
        ho = df['호'].unique()
        df1 = df[(df['동'] == self.CB_outDong.currentText())]
        current_ho = df1['호'].unique()
        self.CB_outHo.clear()
        self.CB_outHo.addItems(current_ho)

    def comboBox_9Init(self):
        df = self.in_df()
        items = df['품명'].unique()
        items.sort()
        self.CB_outItems.clear()
        self.CB_outItems.addItems(items)
        df1 = df[(df['품명'] == self.CB_outItems.currentText())]
        spec = df1['규격'].unique()
        spec.sort()
        self.CB_outSpecs.clear()
        self.CB_outSpecs.addItems(spec)

    def comboBox_9Activated(self):
        df = self.in_df()
        items = df['품명'].unique()
        items.sort()
        df1 = df[(df['품명'] == self.CB_outItems.currentText())]
        spec = df1['규격'].unique()
        spec.sort()
        self.CB_outSpecs.clear()
        self.CB_outSpecs.addItems(spec)

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

    def comboInItemsActivated(self):
        df = self.in_df()
        df = df[(df['품명'] == self.comboInItems.currentText())]
        items = df['품명'].unique()
        items.sort()
        spec = df['규격'].unique()
        spec.sort()
        self.comboInSpecs.clear()
        self.comboInSpecs.addItems(spec)

    def init_in_data_input(self):
        self.in_combo_items_spec()
        df = self.in_df()
        headers = HEADERS[0]#df.columns.values.tolist()
        self.tableWidgetInIn.setHorizontalHeaderLabels(headers)
        df[['입고수량', '구입금액','단가']] = df[['입고수량', '구입금액','단가']].astype('str')
        df.fillna(' ')
        list = df.values.tolist()
        #self.tableWidgetInIn.horizontalHeaderItem().setSectionResizeMode(QHeaderView.Stretch)
        for d in list:
            self.set_tableWidgetInIn(d)
        self.table_display_in()
        self.tableWidgetInIn.scrollToBottom

    def in_combo_items_spec(self):
        df = self.in_df()
        items = df['품명'].unique()
        items.sort()
        self.comboInItems.clear()
        self.comboInItems.addItems(items)    
        df = df[(df['품명'] == self.comboInItems.currentText())]
        spec = df['규격'].unique()
        spec.sort()
        self.comboInSpecs.addItems(spec)

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
        rowcount = self.tableWidgetInIn.rowCount()
        colcount = self.tableWidgetInIn.columnCount()
        headers = HEADERS[0]
        print(headers)
        #headers = [self.tableWidgetInIn.horizontalHeaderItem(x).text() for x in range(0,colcount)]
        data_list = []
        for i in range(0, rowcount):
            data =[]
            for j in range(0, colcount):
                try:
                    d = self.tableWidgetInIn.item(i,j).text()
                except:
                    d=''
                data.append(d)
            print(data)
            data_list.append(data)
        df = pd.DataFrame(data_list) # list to dataframe
        df.columns = headers # set the hwaders on dataframe
        return df

    def lineEditChanged(self):
        try:
            if len(self.LE_InPrice.text())==0:
                pass
        except:
            in_qty = self.LE_InQty.text()
            in_price = self.LE_InPrice.text()
            unit_p = str(round(int(in_price)/int(in_qty)))
            self.LE_InUnitPrice.setText(unit_p)
            return

    def lineEdit_2Changed(self):
        try:
            in_qty = self.LE_InQty.text()
            in_price = self.LE_InPrice.text()
            unit_p = str(round(int(in_price)/int(in_qty)))
            self.LE_InUnitPrice.setText(unit_p)
        except:
            QMessageBox.about(self, "경고", "가격 및 수량 자료를 입력하세요")
            return

    def addComboBoxItem(self) :
        '''
        This function uses to add the new items
        '''
        if len(self.LE_NewInItems.text()) == 0:
            QMessageBox.about(self, "경고", "신규 항목자료를 입력하세요")
            return
        else:
            self.comboInItems.addItem(self.LE_NewInItems.text())
            self.LE_NewInItems.setText('')
    
    def addComboBoxSpecItem(self):
        if len(self.LE_NewInSpecs.text()) == 0:
            QMessageBox.about(self, "경고", "신규 규격 자료를 입력하세요")
            return
        else:
            self.comboInSpecs.addItem(self.LE_NewInSpecs.text())
            self.LE_NewInSpecs.setText('')
    
    def addInMaterialToTable(self):
        
        in_data = []
        #in_data.append('입고')
        in_data.append(self.inDate.text())
        #time = QTime.currentTime()
        #in_data.append(time.toString())
        in_data.append(self.comboInItems.currentText())
        in_data.append(self.comboInSpecs.currentText())
        if len(self.LE_InQty.text())==0:
            QMessageBox.about(self, "경고", "수량 자료를 입력하세요")
            return
        else:
            in_data.append(self.LE_InQty.text())
        if len(self.LE_InPrice.text())==0:
            QMessageBox.about(self, "경고", "가격 자료를 입력하세요")
            return
        else:
            in_data.append(self.LE_InPrice.text())
        in_data.append(self.LE_InUnitPrice.text())
        if len(self.LE_InSupplier.text())==0:
            in_data.append('*')
        else:
            in_data.append(self.LE_InSupplier.text())
        if len(self.LE_InRemarks.text())==0:
            in_data.append('*')
        else:
            in_data.append(self.LE_InRemarks.text())

        self.set_tableWidgetInIn(in_data)
        self.inTableToSaveExcelFile()
    
    def set_tableWidgetInIn(self,data):
        rowCount = self.tableWidgetInIn.rowCount()
        self.tableWidgetInIn.setRowCount(rowCount+1)
        self.tableWidgetInIn.setColumnCount(len(data))
        c = 0
        for i in data:
            self.tableWidgetInIn.setItem(rowCount, c, QTableWidgetItem(i))
            c = c+1
        self.table_display_in()

    def table_display_in(self):
        header = self.tableWidgetInIn.horizontalHeader()
        twidth = header.width()
        width = []
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            width.append(header.sectionSize(column))
        
        wfactor = int(twidth / sum(width))
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            header.resizeSection(column, width[column]*wfactor)
        self.tableWidgetInIn.scrollToBottom

if __name__ == "__main__":
    app = QApplication(sys.argv)
    elWindow = MatWindow()
    elWindow.show()
    app.exec_()