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

        data = self.read_data()
        rdr_row = len(data)
        rdr_col = len(data[0])

        self.tableWidget.setRowCount(rdr_row)
        self.tableWidget.setColumnCount(rdr_col)
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
        row_content = []
        #range(self.tableWidget.columnCount())
        for column in range(self.tableWidget.columnCount()):
            content = self.tableWidget.item(row, column)
            row_content.append(content)

        self.lineEdit_1.setText(row_content[0].text())
        self.lineEdit_2.setText(row_content[1].text())
        self.dateEdit_4.setText(row_content[2].text())
        self.lineEdit_4.setText(row_content[3].text())
        
        #print("cell changed event 발생 : ", row, col, data.text(), lineEditNo)


    def read_data(self):

        filename = resource_path('dowstocks.csv')
        with open(filename, 'r') as f:
            data = []
            for line in f:
                l = line.split(',')
                #print(l)
                items = []
                for item in l:
                    items.append(item)
                    #print(items)
                data.append(items)
        print(data)
        return data

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()
