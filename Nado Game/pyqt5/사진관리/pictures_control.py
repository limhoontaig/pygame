import sys
import os
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal
from PyQt5 import uic
from datetime import datetime

def resource_path(relative_path):
    base_path = getattr(sys, "_MAIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form = resource_path("Pictures.ui")
form_class = uic.loadUiType(form)[0]
# form_1 = resource_path("elec_file_verify.ui")
# form_class_1 = uic.loadUiType(form_1)[0]

now = datetime.now()
yyyymm = now.strftime("%Y")+now.strftime("%m")+'월'
yyyymmdd = now.strftime("%Y")+now.strftime("%m")+'월'+ now.strftime("%D")+'일'
yyyy = now.strftime("%Y")

LE =  [
    'E:/사진',
    'E:/사진정리'
    ]


class ElWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.LE = LE
        self.setupUi(self)

        self.lineEdit.setText(LE[0])
        self.lineEdit_2.setText(LE[1])
        issued = '프로그램 작성 : 임훈택 Rev 0 '+ yyyymmdd + ' Issued'
        self.label.setText(issued)

        self.pushButton.clicked.connect(self.add_file)
        self.pushButton_2.clicked.connect(self.add_file)
        self.pushButton_3.clicked.connect(self.copy_start)
        self.pushButton_4.clicked.connect(self.move_start)

    @pyqtSlot()
    def add_file(self):

        sname = self.sender().text()

        if sname == '원본 폴더':
            init_dir = self.LE[0]
            fname = QFileDialog.getExistingDirectory(self, '엑셀 데이타 파일을 선택하세요', init_dir)
            if len(fname) != 0:
                self.lineEdit.setText(fname)
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
    def copy_start(self):
        # 각 옵션들 값을 확인
        f1 = self.lineEdit.text()
        f2 = self.lineEdit_2.text()
        
        # 파일 목록 확인
        if '.xls' not in f1 or f1 == 0:
            QMessageBox.about(self, "경고", "한전 복지감면 파일을 추가하세요")
            return
        
        if '.xls' not in f2 or f2 == 0:
            QMessageBox.about(self, "경고", "한전 감면 종류 파일을 추가하세요")
            return

    def move_start(self):
        pass

        
        return




if __name__ == "__main__":
    app = QApplication(sys.argv)
    elWindow = ElWindow()
    elWindow.show()
    app.exec_()