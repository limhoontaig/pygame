import os
import sys
import csv
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import * 
from PyQt5.QtCore import Qt, QDate

from PyQt5 import uic

def resource_path(relative_path):
    base_path = getattr(sys, "_MAIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form = resource_path('SP_search.ui')
form_class = uic.loadUiType(form)[0]

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])


class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.pushButton_4.clicked.connect(self.set_tbl)
        self.pushButton_5.clicked.connect(self.tableWidget.clear)

    def set_tbl(self):
        '''
        rows = csv.reader(self.read_data())
        headers = next(rows)
        data = []
        for row in rows:
            data.append(row)
        '''
        data = ['동', '호', '동호명', '가구수', '계약\n종별', '요금적용\n전력', '사용량', '기본요금', '전력량\n요금', 
            '기후환경\n요금', '연료비조정\n요금', '필수사용\n공제', '복지추가\n감액', '할인\n구분', '복지할인', '요금개편\n차액', 
            '절전할인', '자동이체\n/인터넷', '단수', '전기요금', '부가세', '전력\n기금', '전기\n바우처', '정산', '출산가구소급', 
            '당월소계']#, 'TV수신료', '청구금액']

        data.append(['동', '호', '동호명', '가구수', '계약\n종별', '요금적용\n전력', '사용량', '기본요금', '전력량\n요금', 
            '기후환경\n요금', '연료비조정\n요금', '필수사용\n공제', '복지추가\n감액', '할인\n구분', '복지할인', '요금개편\n차액', 
            '절전할인', '자동이체\n/인터넷', '단수', '전기요금', '부가세', '전력\n기금', '전기\n바우처', '정산', '출산가구소급', 
            '당월소계'])#, 'TV수신료', '청구금액'])

        rdr_row = len(data)
        rdr_col = len(data[0])

        self.tableWidget.setAlternatingRowColors(True)

        self.tableWidget.setRowCount(rdr_row)
        self.tableWidget.setColumnCount(rdr_col)
        self.tableWidget.setHorizontalHeaderLabels(['기존', '금월'])
        #self.tableWidget.setHorizontalHeaderLabels(headers)
        self.tableWidget.setSortingEnabled(True) # default ; False

        self.tableView = QtWidgets.QTableView()
        self.model = TableModel(data)
        self.tableView.setModel(self.model)

        #self.setCentralWidget(self.tableView)

        r = 0
        for i in data:
            r += 1
            c = 0
            for j in i:
                c += 1
                self.tableWidget.setItem(r-1,c-1,QTableWidgetItem(j))

        self.tableWidget.cellChanged.connect(self.cellChangeFunc)
        self.tableWidget.cellClicked.connect(self.cellClickedFunc)
        self.lineEdit_1.setText('Test 입력')
        #self.show()



    def cellChangeFunc(self, row, col):
        data = self.tableWidget.item(row, col)
        lineEditNo = 'lineEdit_'+str(col)
        self.lineEdit_1.setText(data.text())
        self.lineEdit_2.setText(data.text())
        print("cell changed event 발생 : ", row, col, data.text(), lineEditNo)

    def cellClickedFunc(self, row, col):
        i= 0
        row_content = []
        #range(self.tableWidget.columnCount())
        for column in range(self.tableWidget.columnCount()):
            content = self.tableWidget.item(row, column).text()
            row_content.append(content)
         
        self.lineEdit_1.setText(row_content[0])
        self.lineEdit_2.setText(row_content[1])
        self.lineEdit_3.setText(row_content[2])
        self.lineEdit_4.setText(row_content[3])
        self.lineEdit_5.setText(row_content[4])
        self.lineEdit_6.setText(row_content[5])
        self.lineEdit_7.setText(row_content[6])
        self.lineEdit_8.setText(row_content[7])
        self.lineEdit_9.setText(row_content[8])
        s = row_content[2].split('/')
        print(s)
        # s_d = s.split('/')
        d = QDate(int(s[2]), int(s[0]), int(s[1]))
        self.dateEdit_3.setDate(d)
        
        #print("cell changed event 발생 : ", row, col, data.text(), lineEditNo)


    def read_data(self):
        
        #files = QFileDialog.askopenfilename(title="엑셀 데이타 파일을 선택하세요", \
        #    filetypes=(("EXCEL 파일", "*.xls"),('CSV 파일', '*.csv'), ("EXCEL 파일", "*.xlsx"), ("모든 파일", "*.*")))
        files = QFileDialog.getOpenFileName(self, '파일을 선택하세요.', r'C:/source/pygame/Nado Game/pyqt5' , 'All File(*);; Text File(*.txt);; csv file(*csv) ;; excel file(*xls *xlsx)')
        filename = resource_path(files[0])
        f = open(filename)
            
        return f

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()
