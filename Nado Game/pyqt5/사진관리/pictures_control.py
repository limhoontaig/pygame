import sys
import os
import pathlib
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal
from PyQt5 import uic
from datetime import datetime
from datetime import date
import re
from time import time
import time
import shutil
from PIL import Image
from PIL.ExifTags import TAGS



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
    'c:/사진',
    'c:/사진정리'
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
        # self.lineEdit = QLineEdit(self)
        self.lineEdit.textChanged.connect(self.list_files)
        # self.listwidget = QListWidget(self)
        # self.listwidget.setAlternatingRowColors(True)

    @pyqtSlot()

    def filesList(self):
        root_dir = self.lineEdit.text()
        #if self.checkBox.isChecked() == True:
        #    os.
        return os.walk(root_dir)

    def delimiter_select(self):
        format = self.comboBox_2.currentText()

        if format.find('-') > 0:
            delimiter = '-'
            return delimiter
        elif format.find('_') > 0:
            delimiter = '_'
            return delimiter
        elif format.find('.') > 0:
            delimiter = '.'
            return delimiter
        elif format.find('년') > 0:
            delimiter = ['년','월','일']
            return delimiter
        elif format.find(' ') > 0:
            delimiter = ' '
            return delimiter
        else :
            delimiter = ''
            return delimiter

    def suffixVerify(self, path, f):
        allow_exts = ['.jpg', '.jpeg', '.png', '.gif', '.avi','.mov', '.mp4']
        # f = pathlib.Path(path, name)  # 원본 파일
        src = pathlib.Path(path, f)
        if src.suffix.lower() in allow_exts:
            return f
        else:
            return ""

    def get_remark(self, path):
        if path.find('/') > 0:
            separator = '/'
        if path.find('\\') > 0:
            separator = '\\'

        sub_dir = path.split(separator)
        sub = sub_dir[-1]
        length = len(sub)
        checker1 = re.compile(r'^(19|20\d\d)[-_ ]?(0[1-9]|1[012])[-_ ]?(0[1-9]|[12][0-9]|3[01])([\s])') 
        # checker1 = re.compile(r'^(\d){8}([\s])')
        checker = re.compile(r'^(\d\d)[-_ ]?(0[1-9]|1[012])[-_ ]?(0[1-9]|[12][0-9]|3[01])([\s])')
        # checker1 = re.compile(r'^(\d){6}([\s])') 
        m = checker1.search(sub)
        n = checker.search(sub)
        if n and length > 7:
            remark = ' ' + sub[7:]
        elif m and length > 9:
            remark = ' ' + sub[9:]
        else:
            remark = ''
        # print(remark)
        

        return remark

    def takePictureTime(self, path, f):
        filename = pathlib.Path(path, f)
        try :
            image = Image.open(filename)
            info = image._getexif()
            image.close()
            # 새로운 딕셔너리 생성
            taglabel = {}
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                taglabel[decoded] = value
            s = taglabel['DateTimeOriginal']
            # print(s)
            timestamp = time.mktime(datetime.strptime(s, '%Y:%m:%d %H:%M:%S').timetuple())
        except:
            now = datetime.now()
            timestamp = datetime.timestamp(now)
        
            
        return timestamp


    def estimateDateFromFileName(self, fname):
        folderName = []
        l = self.delimiter_select() # delimiter
        for path, subdirs, files in fname:
            for file in files:
                f = self.suffixVerify(path, file)
                if f == "":
                    pass
                else:
                    # 기존 폴더에 설명이 있을 경우 가져옴
                    remark = self.get_remark(path)
                    # r_len = len(remark)
                    '''if r_len == 0 and self.checkBox_2.isChecked() == True:
                        remark = ' ' + self.lineEdit_3.text()
                        print (remark)'''
                    # 파일 이름에 날짜 형식이 들어가 있는지 검사하여 디렉토리 생성
                    checker = re.compile(r'(19|20\d\d)[-_ ]?(0[1-9]|1[012])[-_ ]?(0[1-9]|[12][0-9]|3[01])')  
                    m = checker.search(f)

                    if m : # delimiter 종류에 따른 디렉토리 생성 
                        if l[0] == '년':
                            folderName.append([path, m.group(1)+l[0], m.group(1)+l[0]+m.group(2)+l[1], m.group(1)+l[0]+m.group(2)+l[1]+m.group(3)+l[2]+remark, f])
                        else :
                            folderName.append([path, m.group(1), m.group(1)+l+m.group(2), m.group(1)+l+m.group(2)+l+m.group(3)+remark, f])
                    else: # 파일 이름에 날짜가 없을 경우 파일 생성 날짜를 유추하여 파일 디렉토리 생성
                        filename = os.path.join(path, f)
                        # 사진찍은 날짜 가져오기
                        t_time = self.takePictureTime(path, f)
                        # print (filename)
                        c_time = os.path.getctime(filename)
                        m_time = os.path.getmtime(filename)
                        a_time = os.path.getatime(filename)
                        # (t_time, c_time, m_time, a_time)
                        min_time = min(t_time, c_time, m_time, a_time)
                        dt = datetime.fromtimestamp(min_time)
                        if l[0] == '년':
                            y = dt.strftime("%Y"+l[0])
                            ym = dt.strftime("%Y"+l[0]+"%m"+l[1])
                            ymd = dt.strftime("%Y"+l[0]+"%m"+l[1]+"%d"+l[2]+remark)
                        else:
                            y = dt.strftime("%Y")
                            ym = dt.strftime("%Y"+l+"%m")
                            ymd = dt.strftime("%Y"+l+"%m"+l+"%d"+remark)
                        folderName.append([path, y, ym, ymd, f])
        return folderName

    def copyFile(self, folderName):
        for folder in folderName:
            target_folder = self.lineEdit_2.text()
            f = pathlib.Path(folder[0], folder[4])
            folder_tree = self.folder_tree()
            if folder_tree == 'ymd':
                t = pathlib.Path(target_folder,folder[1],folder[2], folder[3])
            elif folder_tree == 'ym':
                t = pathlib.Path(target_folder,folder[1],folder[2])
            else:
                t = pathlib.Path(target_folder,folder[1])

            # 분류될 경로 생성
            t.mkdir(parents=True, exist_ok=True) # 파일 경로에 있는 모든 폴더를 생성함. 있으면 놔둠
            if os.isfile(pathlib.Path(t, folder[4])):
                pass
            else:
                shutil.copy2(f, t) # 파일 복사 (파일 개정 시간 등 포함하여 복사를 위해 copy2 사용)

    def moveFile(self, folderName):
        for folder in folderName:
            target_folder = self.lineEdit_2.text()
            f = pathlib.Path(folder[0], folder[4]) # source file 경로 및 이름
            folder_tree = self.folder_tree()
            if folder_tree == 'ymd':
                t = pathlib.Path(target_folder,folder[1],folder[2], folder[3])
            elif folder_tree == 'ym':
                t = pathlib.Path(target_folder,folder[1],folder[2])
            else:
                t = pathlib.Path(target_folder,folder[1])
            t_file = pathlib.Path(t, folder[4]) # target file 경로 및 이름 
            # 분류될 경로 생성
            t.mkdir(parents=True, exist_ok=True) # 파일 경로에 있는 모든 폴더를 생성함. 있으면 놔둠
            #shutil.move(f, t_file) # 파일 이동 후 원본 삭제

    def folder_tree(self):
        folder_tree = self.comboBox.currentText()
        # print(folder_tree)

        if folder_tree.find('년/월/일별로 정리') >= 0:
            folder_tree_type = 'ymd'
            return folder_tree_type
        elif folder_tree.find('년/월별로 정리') >= 0:
            folder_tree_type = 'ym'
            return folder_tree_type
        else:
            folder_tree_type = 'y'
            return folder_tree_type

    def copy_start(self):
        fl = self.filesList()
        folderName = self.estimateDateFromFileName(fl)
        self.copyFile(folderName)
        QMessageBox.about(self, "복사 완료", "파일 복사가 완료 되었습니다")
        self.listWidget.clear()
        return


    def move_start(self):
        fl = self.filesList()
        #fl = self.suffixVerify(flist)
        folderName = self.estimateDateFromFileName(fl)
        self.moveFile(folderName)
        QMessageBox.about(self, "이동 완료", "파일 이동이 완료 되었습니다")
        self.listWidget.clear()
        return



    def add_file(self):
        sname = self.sender().text()
        if sname == '원본 폴더':
            init_dir = self.LE[0]
            fname = QFileDialog.getExistingDirectory(self, '원본 사진 파일이 있는 디렉토리를 선택하세요', init_dir)
            if len(fname) != 0:
                self.lineEdit.setText(fname)
            else:
                self.lineEdit.setText(LE[0])
        else :
            # sname == '정리할 폴더':
            init_dir = self.LE[1]
            fname = QFileDialog.getExistingDirectory(self, '사진 파일을 정리해 놓을 디렉토리를 선택하세요', init_dir)
            if len(fname[0]) != 0:
                self.lineEdit_2.setText(fname)
            else:
                self.lineEdit_2.setText(LE[1])

    def list_files(self):
        fl = self.filesList()
        self.listWidget.clear()
        self.listWidget.setAlternatingRowColors(True)
        for path, subdir, file in fl:
            for f in file:
                self.addListWidget(path, f)

    def addListWidget(self, path, f):
        #print(path, f)
        self.addItemText = path + " " + f
        #print (self.addItemText)
        self.listWidget.addItem(self.addItemText)

            

if __name__ == "__main__":
    app = QApplication(sys.argv)
    elWindow = ElWindow()
    elWindow.show()
    app.exec_()