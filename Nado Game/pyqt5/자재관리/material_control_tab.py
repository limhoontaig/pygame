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
    ['품명','규격','입고수량','사용수량','재고','비고'],
    ['입출','일자','품명','규격','입고수량','누계입고','구입금액','단가','구입업체','비고'],
    ['입출','일자','공용','동','호', '품명', '규격', '사용수량', '사용누계', '비고', ],
    ['일자', '품명', '규격','입출', '입고수량','구입금액','단가','동', '호', '공용','사용수량', '재고']
]


class MatWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.LE = LE
        self.HEADERS = HEADERS
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
        self.checkBox.stateChanged.connect(self.setInUsedStartDate)
        self.checkBox_2.stateChanged.connect(self.setDetailedStartDate)

        self.init_in_data_input()
        self.init_out_data_input()
        self.init_onstock_query()
        self.init_in_query()
        self.init_detailed_total_query()

        
        #self.onstockDate.selectionChanged.connect(self.set_calendar_today_color)
        #입고품목 선택시 품목 규격 콤보박스 항목 선택
        self.CB_onstockItems.activated.connect(self.onstock_query_combo_spec)
        #입고품목 선택시 품목 규격 콤보박스 항목 선택
        self.CB_inUsedQueryItems.activated.connect(self.in_query_combo_spec)
        #입고품목 선택시 품목 규격 콤보박스 항목 선택
        self.CB_detailedQueryItems.activated.connect(self.in_out_query_combo_spec)
        #입고품목 선택시 품목 규격 콤보박스 항목 선택
        self.CB_detailedQuerySpecs.activated.connect(self.detailed_total_query)
        #입고품목 선택시 품목 규격 콤보박스 항목 선택
        self.comboInItems.activated.connect(self.comboInItemsActivated)
        #입고 품목 선택시 품목 재고 보임
        self.comboInItems.activated.connect(self.in_stock_view)
        #입고 품목규격 선택시 품목 재고 보임
        self.comboInSpecs.activated.connect(self.in_stock_view)
        #사용 품목규격 선택시 품목 재고 보임
        self.CB_outItems.activated.connect(self.CB_outItemsActivated)
        #사용 품목 선택시 품목 재고 보임
        self.CB_outItems.activated.connect(self.out_stock_view)
        #사용 품목규격 선택시 품목 재고 보임
        self.CB_outSpecs.activated.connect(self.out_stock_view)
        #동 선택시 호수 콤보 선택
        self.CB_outDong.activated.connect(self.out_dongho)

        self.PB_inToday.clicked.connect(self.setInToday)# 오늘날자 설정
        self.PB_inAddNewItem.clicked.connect(self.addComboBoxItem)# 신규 품목 추가
        self.PB_InAddComboBoxSpec.clicked.connect(self.addComboBoxSpecItem) #신규 항목 추가
        self.PB_InAdd.clicked.connect(self.addInMaterialToTable)
        self.PB_InSave.clicked.connect(self.inTableToSaveExcelFile)
        self.PB_InExit.clicked.connect(self.close)

        self.PB_outTableToSaveFile.clicked.connect(self.outTableToSaveExcelFile)
        self.PB_onstockQuery.clicked.connect(self.onstock_view)# 자재 품목/규격 별 제고 조회
        self.PB_inUsedQuery.clicked.connect(self.in_out_status_view) # 품목/규격 별 자대 입고 현황 조회 
        self.PB_detailedQuery.clicked.connect(self.detailed_total_query) # 품목/규격 별 자대 입고 현황 조회 
        self.pushButton_11.clicked.connect(self.addOutMaterialToTable)
        self.LE_InQty.textChanged.connect(self.lineEditChanged)
        self.LE_InPrice.textChanged.connect(self.lineEdit_2Changed)


    def setInToday(self):
        self.inDate.setDate(QDate.currentDate())


    def init_detailed_total_query(self):
        self.in_out_query_combo_items_spec()
        self.detailedQueryTableWidget.setColumnCount(len(HEADERS[5]))
        headers = HEADERS[5]#df_in_out.columns.values.tolist()
        self.detailedQueryTableWidget.setHorizontalHeaderLabels(headers)
        df_list = self.detailed_in_out_list()
        if len(df_list)==0:
            return
        df_in_out = self.detailed_in_out_df(df_list)
        df_in_out_values_list = df_in_out.values.tolist()
        for i in df_in_out_values_list:
            self.set_detailedQueryTableWidget(i)
        self.table_display_detailedQueryTableWidget()

    def detailed_total_query(self):
        df_list = self.detailed_in_out_list()
        df_in_out = self.detailed_in_out_df(df_list)
        if len(df_in_out) == 0:
            QMessageBox.about(self, "경고", "검색 기간 동안 해당 품목에 대한 입출고 기록이 없습니다")
            return
        df_in_out[['입고수량','구입금액','단가','동','사용수량']]=df_in_out[['입고수량','구입금액','단가','동','사용수량']].astype('int')

        df_in_out = df_in_out.fillna(0)

        df_in_out[['입고수량','구입금액','단가','동','사용수량','재고']]=df_in_out[['입고수량','구입금액','단가','동','사용수량','재고']].astype('float')
        df_in_out[['입고수량','구입금액','단가','동','사용수량','재고']]=df_in_out[['입고수량','구입금액','단가','동','사용수량','재고']].astype('int')
        df_in_out[['입고수량','구입금액','단가','동','사용수량','재고']]=df_in_out[['입고수량','구입금액','단가','동','사용수량','재고']].astype('str')

        self.detailedQueryTableWidget.clear()
        self.detailedQueryTableWidget.setRowCount(0)
        self.detailedQueryTableWidget.setColumnCount(len(HEADERS[5]))
        self.detailedQueryTableWidget.setHorizontalHeaderLabels(HEADERS[5])
        df_in_out_values_list = df_in_out.values.tolist()
        for i in df_in_out_values_list:
            self.set_detailedQueryTableWidget(i)
        self.table_display_detailedQueryTableWidget()


    def on_stock_total(self, dfIn, dfOut):
        df_in = dfIn[['품명','규격', '입고수량']].copy()
        df_in_sum = df_in.groupby(['품명','규격']).sum()

        df_out = dfOut[['품명','규격', '사용수량']].copy()
        df_out_sum = df_out.groupby(['품명','규격']).sum()

        df_on_stock = pd.merge(df_in_sum, df_out_sum, how = 'outer', on = ['품명','규격'])
        df_on_stock.fillna(0, inplace=True)
        date = self.DE_detailedQueryFromDate.date()
        fromQdate = date.addDays(-1)
        from_date =fromQdate.toString(Qt.ISODate) 
        df_on_stock['일자'] = from_date
        try:
            df_on_stock['입출'] = '재고'
            df_on_stock['재고'] = df_on_stock['입고수량'] - df_on_stock['사용수량']
            df_on_stock[['입고수량', '사용수량','재고']] = df_on_stock[['입고수량', '사용수량','재고']].astype('str')
            df_m = df_on_stock.reset_index().copy()
            return df_m
        except:
            pass

    def set_detailedQueryTableWidget(self, df_list):
        rowCount = self.detailedQueryTableWidget.rowCount()
        self.detailedQueryTableWidget.setRowCount(rowCount+1)
        c = 0
        for i in df_list:
            self.detailedQueryTableWidget.setItem(rowCount, c, QTableWidgetItem(i))
            c = c+1
    
    def table_display_detailedQueryTableWidget(self):
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

    def setDetailedStartDate(self, state):
        if state == 2:
            to_date = self.DE_detailedQueryToDate.date()
            first_day = to_date.addDays(1-to_date.day())
            self.DE_detailedQueryFromDate.setDate(first_day)
        else:
            to_date = self.DE_detailedQueryToDate.date()
            from_day = to_date.addMonths(-1)
            self.DE_detailedQueryFromDate.setDate(from_day)

    def df_status_selection(self, df):
        caller_name = sys._getframe(1).f_code.co_name
        from_date = self.DE_detailedQueryFromDate.text()
        to_date = self.DE_detailedQueryToDate.text()
        
        items = self.CB_detailedQueryItems.currentText()
        spec = self.CB_detailedQuerySpecs.currentText()
        date_to_con = df['일자'] <= to_date
        date_from_con = df['일자'] >= from_date
        i_con = df['품명'] == items
        s_con = df['규격'] == spec
        if caller_name == 'on_stock_total':
            date = self.DE_detailedQueryFromDate.date()
            fromQdate = date.addDays(-1)
            from_date = fromQdate.toString(Qt.ISODate)
            df_sel = df[((df['일자'] <= from_date) & i_con & s_con)]
            return df_sel
        #else:
        if items == 'All':
            df_sel = df[(date_from_con & date_to_con)]
            df_onstock = df[(df['일자'] <= from_date)]
            return df_sel, df_onstock
        else:
            df_sel = df[(date_from_con & date_to_con & i_con & s_con)]
            df_onstock = df[((df['일자'] <= from_date) & i_con & s_con)]
            return df_sel, df_onstock

    def detailed_in_out_list(self):
        dfI = self.in_df()
        dfI['입출'] ='입고'
        dfIn_on = self.df_status_selection(dfI)
        dfIn = dfIn_on[0]
        dfInOn = dfIn_on[1]
        dfO = self.out_df()
        dfO['입출'] = '사용'
        dfOut_on = self.df_status_selection(dfO)
        dfOut = dfOut_on[0]
        dfOutOn = dfOut_on[1]
        items_in = set(dfIn['품명'].unique())
        items_out = set(dfOut['품명'].unique())
        items = list(items_in.union(items_out))
        df_list = []
        for item in items:
            dfInSpec = dfIn[(dfIn['품명'] == item)]
            dfOutSpec = dfOut[(dfOut['품명'] == item)]
            specs_in = set(dfInSpec['규격'].unique())
            specs_out = set(dfOutSpec['규격'].unique())
            specs = list(specs_in.union(specs_out))
            for spec in specs:
                dfIn_sel = dfIn[((dfIn['품명'] == item) & (dfIn['규격'] == spec))]
                dfOut_sel = dfOut[((dfOut['품명'] == item) & (dfOut['규격'] ==  spec))]
                df_on_stock = pd.merge(dfIn_sel, dfOut_sel, how = 'outer', on = ['입출','일자','품명','규격'])
                df_on_stock.fillna(0, inplace=True)
                df_on_stock.sort_values(by= '일자', inplace=True)
                df_total = df_on_stock[['일자','품명','규격','입출','입고수량','구입금액','단가','동','호','공용','사용수량']].copy()
                df_total.reset_index(drop=True, inplace=True)

                df_total[['입고수량','구입금액','단가','동','사용수량']] = df_total[['입고수량','구입금액','단가','동','사용수량']].astype('int')
                df_total[['입고수량','구입금액','단가','동','사용수량']] = df_total[['입고수량','구입금액','단가','동','사용수량']].astype('str')

                dfInOnSel = dfInOn[((dfInOn['품명'] == item) & (dfInOn['규격'] == spec))]
                dfOutOnSel = dfOutOn[((dfOutOn['품명'] == item) & (dfOutOn['규격'] == spec))]


                df_onstock = self.on_stock_total(dfInOnSel,dfOutOnSel)

                df_total = pd.merge(df_total, df_onstock, how = 'outer', on= ['입출','일자','품명','규격','입고수량','사용수량'])
                df_total.sort_values(by='일자', inplace=True)

                df_total.fillna(0, inplace=True)
                df_total[['입고수량','구입금액','단가','동','사용수량']] = df_total[['입고수량','구입금액','단가','동','사용수량']].astype('float')
                df_total[['입고수량','구입금액','단가','동','사용수량']] = df_total[['입고수량','구입금액','단가','동','사용수량']].astype('int')
                df_total['재고'] = df_total['입고수량'] - df_total['사용수량']
                df_temp = df_total[['재고']].copy()
                df_temp_1  = df_temp.cumsum()
                df_total['재고'] = df_temp_1['재고']
                df_total[['입고수량','구입금액','단가','동','사용수량','재고']] = df_total[['입고수량','구입금액','단가','동','사용수량','재고']].astype('float')
                df_total[['입고수량','구입금액','단가','동','사용수량','재고']] = df_total[['입고수량','구입금액','단가','동','사용수량','재고']].astype('int')
                df_total[['입고수량','구입금액','단가','동','사용수량','재고']] = df_total[['입고수량','구입금액','단가','동','사용수량','재고']].astype('str')
                df_total = df_total[HEADERS[5]]
                if df_total.empty:
                    pass
                else:
                    df_list.append(df_total)
        return df_list

    def detailed_in_out_df(self, df_list):
        if len(df_list) == 0:
            return df_list
        df_con = df_list[0]
        for part in df_list[1:]:
            df_con = pd.concat([df_con, part])
            df_con.reset_index(drop=True, inplace=True)
        df_con[['입고수량','구입금액','단가','동','사용수량']]= df_con[['입고수량','구입금액','단가','동','사용수량']].astype('int')
        df_con[['입고수량','구입금액','단가','동','호','사용수량']] = df_con[['입고수량','구입금액','단가','동','호','사용수량']].astype('str')

        return df_con

    def init_in_query(self):
        self.in_query_combo_items_spec()
        df = self.in_df()
        df_in = self.in_out_status(df)
        if df_in is None:
            return
        self.inUsedTableWidget.clear()
        self.inUsedTableWidget.setColumnCount(len(HEADERS[3]))
        self.inUsedTableWidget.setRowCount(0)
        self.inUsedTableWidget.setHorizontalHeaderLabels(HEADERS[3])
        df_list = df_in.values.tolist()
        for list in df_list:
            self.set_inUsedTableWidge(list)
        self.table_display_status()
    
    def in_out_status_view(self):
        if self.CB_inUsedInOut.currentText() == '입고':
            #self.init_in_query()
            df_sel = self.detailed_in_view()
            if len(df_sel) ==0:
                QMessageBox.about(self, "경고", "검색기간에 입고 자료가 없습니다")
                return
            self.inUsedTableWidget.clear()
            self.inUsedTableWidget.setColumnCount(len(HEADERS[3]))
            self.inUsedTableWidget.setRowCount(0)
            self.inUsedTableWidget.setHorizontalHeaderLabels(HEADERS[3])
            df_list = self.detailed_in_out_concat_df(df_sel)
            df_list = df_list.values.tolist()
            for l in df_list:
                self.set_inUsedTableWidge(l)
            self.table_display_status()
            
        else:
            df_sel = self.detailed_out_view()
            if len(df_sel) ==0:
                QMessageBox.about(self, "경고", "검색기간에 사용 자료가 없습니다")
                return
            headers = HEADERS[4]
            colcount = len(headers)
            self.inUsedTableWidget.clear()
            self.inUsedTableWidget.setColumnCount(colcount)
            self.inUsedTableWidget.setRowCount(0)
            self.inUsedTableWidget.setHorizontalHeaderLabels(headers)
            df_list = self.detailed_in_out_concat_df(df_sel)
            df_list = df_list.values.tolist()
            for l in df_list:
                self.set_inUsedTableWidge(l)
            self.table_display_status()

    def setInUsedStartDate(self, state):
        if state == 2:
            to_date = self.DE_inUsedQueryToDate.date()
            first_day = to_date.addDays(1-to_date.day())
            self.DE_inUsedQueryFromDate.setDate(first_day)
        else:
            to_date = self.DE_inUsedQueryToDate.date()
            from_day = to_date.addMonths(-1)
            self.DE_inUsedQueryFromDate.setDate(from_day)


    def df_in_out_selection(self, df):
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


    def detailed_in_out_concat_df(self, df_list):
        if len(df_list) == 0:
            return df_list
        df_con = df_list[0]
        for part in df_list[1:]:
            df_con = pd.concat([df_con, part])
            df_con.reset_index(drop=True, inplace=True)
        return df_con

    def detailed_in_view(self):
        dfI = self.in_df()
        dfI['입출'] ='입고'
        dfI.rename(columns = {'입고일':'일자'}, inplace=True)
        dfIn = self.df_in_out_selection(dfI)
        items = set(dfIn['품명'].unique())
        specs = set(dfIn['규격'].unique())
        temp_list = []
        for item in items:
            for spec in specs:
                dfIn_sel = dfIn[((dfIn['품명'] == item) & (dfIn['규격'] == spec))].copy()
                dfIn_sel['누계입고'] = dfIn_sel['입고수량'].cumsum()
                dfIn_sel=dfIn_sel[HEADERS[3]]
                dfIn_sel[['입고수량','누계입고','구입금액','단가']]= dfIn_sel[['입고수량','누계입고','구입금액','단가']].astype('int')
                dfIn_sel[['입고수량','누계입고','구입금액','단가']] = dfIn_sel[['입고수량','누계입고','구입금액','단가']].astype('str')
                temp_list.append(dfIn_sel)
        return temp_list 
        
    def detailed_out_view(self):
        dfO = self.out_df()
        dfO['입출'] = '사용'
        dfO.rename(columns = {'사용일':'일자'}, inplace=True)
        dfOut = self.df_in_out_selection(dfO)
        items = set(dfOut['품명'].unique())
        specs = set(dfOut['규격'].unique())
        temp_list = []
        for item in items:
            for spec in specs:
                dfOut_sel = dfOut[((dfOut['품명'] == item) & (dfOut['규격'] ==  spec))]
                dfOut_sel = dfOut[((dfOut['품명'] == item) & (dfOut['규격'] == spec))]
                dfOut_sel['사용누계'] = dfOut_sel['사용수량'].cumsum()
                columns = dfOut_sel.columns.tolist()
                dfOut_sel = dfOut_sel[HEADERS[4]]
                dfOut_sel[['동','사용수량','사용누계']]= dfOut_sel[['동','사용수량','사용누계']].astype('int')
                dfOut_sel[['동','사용수량','사용누계']] = dfOut_sel[['동','사용수량','사용누계']].astype('str')
                temp_list.append(dfOut_sel)
        return temp_list     

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
        if len(df_lists) == 0:
            return
        
        df_con = df_lists[0]
        for df_list in df_lists[1:]:
            df_con = pd.concat([df_con, df_list])
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

    def init_onstock_query(self):
        self.onstock_query_combo_items_spec()
        df = self.on_stock()
        if df is None:
            QMessageBox.about(self, "경고", "입고출고 자료가 없습니다")
            return
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
        self.onstockTableWidget.setColumnCount(len(HEADERS[2]))
        headers = HEADERS[2]#[self.onstockTableWidget.horizontalHeaderItem(x).text() for x in range(0,colcount)]
        self.onstockTableWidget.clear()
        self.onstockTableWidget.setRowCount(0)
        self.onstockTableWidget.setHorizontalHeaderLabels(headers)
        df_sel = self.df_onstock_selection()
        if df_sel is None:
            QMessageBox.about(self, "경고", "입출고 자료가 없습니다")
            return
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
            df_on_stock[['입고수량', '사용수량','재고']] = df_on_stock[['입고수량', '사용수량','재고']].astype('int')
            df_on_stock[['입고수량', '사용수량','재고']] = df_on_stock[['입고수량', '사용수량','재고']].astype('str')
            df_m = df_on_stock.reset_index().copy()
            return df_m
        except:
            pass
                    
    def set_onstockTableWidget(self,df_list):
        rowCount = self.onstockTableWidget.rowCount()
        self.onstockTableWidget.setRowCount(rowCount+1)
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
        self.out_dongho()
        self.CB_outGongSe.clear()
        self.CB_outGongSe.addItems(['공용','세대'])
        self.out_combo_items_spec()

        headers = HEADERS[1]
        self.usedIntableWidget.setHorizontalHeaderLabels(headers)
        df = self.out_df()
        df[['사용수량', '동']] = df[['사용수량', '동']].astype('str')
        df.fillna(' ')


        self.out_file_to_table(df)
        self.table_display_used_in()
        
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
        self.usedIntableWidget.setColumnCount(len(HEADERS[1]))
        c = 0
        for i in data:
            self.usedIntableWidget.setItem(rowCount, c, QTableWidgetItem(i))
            c = c+1
        
        self.table_display_used_in()

    def table_display_used_in(self):
        header = self.usedIntableWidget.horizontalHeader()
        twidth = header.width()
        width = []
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            width.append(header.sectionSize(column))
        
        wfactor = int(twidth / sum(width))
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            header.resizeSection(column, width[column]*wfactor)
        self.usedIntableWidget.scrollToBottom

    def out_file_to_table(self, df):
        df[['동','사용수량']] = df[['동','사용수량']].astype('int')
        df[['동', '호','사용수량']] = df[['동', '호','사용수량']].astype('str')
        df.fillna(' ')
        list = df.values.tolist()

        for d in list:
            self.set_usedIntableWidget(d)
        self.usedIntableWidget.scrollToBottom

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

    def CB_outItemsInit(self):
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

    def CB_outItemsActivated(self):
        df = self.in_df()
        items = df['품명'].unique()
        items.sort()
        df1 = df[(df['품명'] == self.CB_outItems.currentText())]
        spec = df1['규격'].unique()
        spec.sort()
        self.CB_outSpecs.clear()
        self.CB_outSpecs.addItems(spec)

    def out_df(self):
        file = LE[1] 
        with pd.ExcelFile(file) as f:
            df = pd.read_excel(f,skiprows=0)
            if df is None:
                return
        return df

    def in_df(self):
        file = LE[0] 
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
        headers = HEADERS[0]
        self.tableWidgetInIn.setHorizontalHeaderLabels(headers)
        df[['입고수량', '구입금액','단가']] = df[['입고수량', '구입금액','단가']].astype('str')
        df.fillna(' ')
        list = df.values.tolist()
        for d in list:
            self.set_tableWidgetInIn(d)
            self.table_display_in()
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
        file = LE[0]
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
        data_list = []
        for i in range(0, rowcount):
            data =[]
            for j in range(0, colcount):
                try:
                    d = self.tableWidgetInIn.item(i,j).text()
                except:
                    d=''
                data.append(d)
            data_list.append(data)
        df = pd.DataFrame(data_list) 
        df.columns = headers 
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
        in_data.append(self.inDate.text())
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
        self.table_display_in()
    
    def set_tableWidgetInIn(self,data):
        rowCount = self.tableWidgetInIn.rowCount()
        self.tableWidgetInIn.setRowCount(rowCount+1)
        c = 0
        for i in data:
            self.tableWidgetInIn.setItem(rowCount, c, QTableWidgetItem(i))
            c = c+1

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