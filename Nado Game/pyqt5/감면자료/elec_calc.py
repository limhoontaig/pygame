import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal
from PyQt5 import uic


def resource_path(relative_path):
    base_path = getattr(sys, "_MAIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
form = resource_path("전기감면_mainwindow.ui")
form_class = uic.loadUiType(form)[0]

from datetime import datetime
now = datetime.now()
yyyymm = now.strftime("%Y")+now.strftime("%m")+'월'
yyyy = now.strftime("%Y")

class CustomSignal(QObject):



    signal = pyqtSignal(int, str) #반드시 클래스 변수로 선언할 것 
    def run(self): 
        LE =  [
            'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/한전부과자료',
            'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/한전부과자료',
            'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/xperp_감면자료',
            'D:/과장/1 1 부과자료/'+yyyy+'년/Templates/Elec_Template_File_for_XPERP_upload.xls'
            ]
        tempstr = LE
        for i, tempstr in LE: 
            self.signal.emit(i, tempstr) #customFunc 메서드 실행시 signal의 emit 메서드사용


class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.lineEdit.setText('D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/한전부과자료')
        self.lineEdit_2.setText('D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/한전부과자료')
        self.lineEdit_3.setText('D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/xperp_감면자료')
        self.lineEdit_4.setText('D:/과장/1 1 부과자료/'+yyyy+'년/Templates/Elec_Template_File_for_XPERP_upload.xls')

        self.pushButton.clicked.connect(self.add_file)
        self.pushButton_2.clicked.connect(self.add_file)
        self.pushButton_3.clicked.connect(self.add_file)
        self.pushButton_4.clicked.connect(self.add_file)

    @pyqtSlot(int, str)
    def add_file(self, i, tmpstr):
        self.i = i
        self.tmpstr = tmpstr
        init_dir = self.tmpstr.text()
        fname = QFileDialog.getOpenFileName(self, 'Open File', init_dir, 'Excel (*.xls *.xlsx)')
        if i == 0:
            self.lineEdit.setText(fname[0])
        elif i == 1:
            self.lineEdit_2.setText(fname[0])
        elif i == 2:
            self.lineEdit_3.setText(fname[0])
        else:
            self.lineEdit_4.setText(fname[0])


'''
        if kind == 'welfare':
            self.lineEdit.setText(fname[0])
            return self.lineEdit.text()

        elif kind == 'kind':
            txt_kind_welfare_path.delete(0,END)
            txt_kind_welfare_path.insert(0, files)
            return txt_kind_welfare_path

        else:
            txt_template_path.delete(0,END)
            txt_template_path.insert(0, files)
            return txt_template_path   
'''

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()