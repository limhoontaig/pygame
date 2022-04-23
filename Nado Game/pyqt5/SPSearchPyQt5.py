import os
import sys
import csv
from PyQt5.QtWidgets import *
from PyQt5 import uic

def resource_path(relative_path):
    base_path = getattr(sys, "_MAIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form = resource_path('SP_search.ui')
form_class = uic.loadUiType(form)[0]

class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        rows = csv.reader(self.read_data())
        headers = next(rows)
        data = []
        for row in rows:
            data.append(row)
        rdr_row = len(data)
        rdr_col = len(data[0])

        self.tableWidget.setAlternatingRowColors(True)

        self.tableWidget.setRowCount(rdr_row)
        self.tableWidget.setColumnCount(rdr_col)
        self.tableWidget.setHorizontalHeaderLabels(headers)
        self.tableWidget.setSortingEnabled(True) # default ; False
        r = 0
        for i in data:
            r += 1
            c = 0
            for j in i:
                c += 1
                self.tableWidget.setItem(r-1,c-1,QTableWidgetItem(j) )

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
            content = self.tableWidget.item(row, column)
            row_content.append(content)
         
        self.lineEdit_1.setText(row_content[0].text())
        self.lineEdit_2.setText(row_content[1].text())
        self.lineEdit_3.setText(row_content[2].text())
        self.lineEdit_4.setText(row_content[3].text())
        self.lineEdit_5.setText(row_content[4].text())
        self.lineEdit_6.setText(row_content[5].text())
        self.lineEdit_7.setText(row_content[6].text())
        self.lineEdit_8.setText(row_content[7].text())
        self.lineEdit_9.setText(row_content[8].text())
        
        #print("cell changed event 발생 : ", row, col, data.text(), lineEditNo)


    def read_data(self):
        
        #files = QFileDialog.askopenfilename(title="엑셀 데이타 파일을 선택하세요", \
        #    filetypes=(("EXCEL 파일", "*.xls"),('CSV 파일', '*.csv'), ("EXCEL 파일", "*.xlsx"), ("모든 파일", "*.*")))
        files = QFileDialog.getOpenFileName(self)
        filename = resource_path(files[0])
        f = open(filename)
            
        return f

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()
