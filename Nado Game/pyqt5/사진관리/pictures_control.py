import sys
import os
import stat
import pathlib
import pandas as pd
from PyQt5.QtCore import Qt, pyqtSlot, QObject, pyqtSignal
from PyQt5 import uic
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QAction, \
    qApp, QFileDialog, QApplication

from datetime import datetime
from datetime import date
import re
from time import time
import time
import shutil
from PIL import Image
from PIL.ExifTags import TAGS
import pandas as pd

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
TEMPFILE = 'TEMP_EXCEL_FileList.xlsx'

class ElWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.LE = LE
        self.TEMPFILE = TEMPFILE
        self.setupUi(self)

        self.lineEdit.setText(LE[0])
        self.lineEdit_2.setText(LE[1])
        issued = '프로그램 작성 : 임훈택 Rev 0 '+ yyyymmdd + ' Issued'
        self.label.setText(issued)
        self.scaleFactor = 1.0
        
        #self.imageLabel = QLabel()
        self.label_8.setBackgroundRole(QPalette.Base)
        #self.label_8.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        #self.label_8.setScaledContents(True)

        #pixmap = QPixmap()
        #if pixmap == None:
        self.disablePushButton()

        '''
        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.label_8)
        self.setCentralWidget(self.scrollArea)
        '''

        self.pushButton.clicked.connect(self.add_file)
        self.pushButton_2.clicked.connect(self.add_file)
        self.pushButton_3.clicked.connect(self.copy_start)
        self.pushButton_4.clicked.connect(self.move_start)
        self.pushButton_5.clicked.connect(self.list_files) 
        self.pushButton_6.clicked.connect(self.zoomIn) # Zoom in
        self.pushButton_7.clicked.connect(self.zoomOut) # Zoom out
        self.pushButton_8.clicked.connect(self.list_files) # Fit to Label
        self.pushButton_9.clicked.connect(self.fitToWidth) # Fit to width
        self.pushButton_10.clicked.connect(self.list_files) # Fit to Height 
        self.pushButton_11.clicked.connect(self.normalSize) # Fit to Normal size 
        self.pushButton_12.clicked.connect(self.delSelectedFile) # Fit to Normal size 
        self.pushButton_13.clicked.connect(self.delAllOtherFiles) # Fit to Normal size 
        self.listWidget.itemClicked.connect(self.qImageViewer)
        self.disablePBCopyMove()
        self.lineEdit.textChanged.connect(self.enablePBCopyMove)
        # self.listwidget = QListWidget(self)
        # self.listwidget.setAlternatingRowColors(True)

    @pyqtSlot()

    def disablePBCopyMove(self):
        self.pushButton_3.setDisabled(True)
        self.pushButton_4.setDisabled(True)


    def enablePBCopyMove(self):
        self.pushButton_3.setEnabled(True)
        self.pushButton_4.setEnabled(True)

    def disablePushButton(self):
        self.pushButton_6.setDisabled(True) # Zoom in
        self.pushButton_7.setDisabled(True) # Zoom out
        self.pushButton_8.setDisabled(True) # Fit to Label
        self.pushButton_9.setDisabled(True) # Fit to width
        self.pushButton_10.setDisabled(True) # Fit to Height 
        self.pushButton_11.setDisabled(True) # Fit to Normal size 

    def enablePushButton(self):
        self.pushButton_6.setEnabled(True) # Zoom in
        self.pushButton_7.setEnabled(True) # Zoom out
        self.pushButton_8.setEnabled(True) # Fit to Label
        self.pushButton_9.setEnabled(True) # Fit to width
        self.pushButton_10.setEnabled(True) # Fit to Height 
        self.pushButton_11.setEnabled(True) # Fit to Normal size 

    def fitToWidth(self):
        #pixmap = self.makePixmap()
        #self.label_8.resize(pixmap.scaledToWidth(self.label_8.pixmap.size()))
        #self.label_8.resize(pixmap.scaledToWidth(self.label_8.pixmap.size()))
        #pixmap = pixmap.scaledToWidth(660)
        #self.label_8.pixmap.setToWidth()
        pass


    def fitToHeight(self):
        return
        pixmap = self.makePixmap()
        #self.label_8.resize(pixmap.scaledToHeight(self.label_8.pixmap.size()))
        pixmap = pixmap.scaledToHeight(460)

    def normalSize(self):
        self.label_8.adjustSize()

    def fitToWindow(self):
        fitToWindow = True
        self.label_8.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()
        self.updateActions()

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.label_8.resize(self.scaleFactor * self.label_8.pixmap().size())

        self.pushButton_6.setEnabled(self.scaleFactor < 1.0)
        self.pushButton_7.setEnabled(self.scaleFactor > 0.6)

    def makePixmap(self):    
        file = self.listWidget.currentItem().text()
        path, f = os.path.split(file)
        self.lineEdit_3.setText(self.get_remark(path))
        pixmap = QPixmap(file)
        return pixmap

    def qImageViewer(self):    
        width = 660
        height = 460
        self.label_8.resize(width,height)
        pixmap = self.makePixmap()
        if self.scaleDirection(width, height, pixmap) == 'width':
            pixmap = pixmap.scaledToWidth(width)
        else:
            pixmap = pixmap.scaledToHeight(height)
        self.label_8.setPixmap(QPixmap(pixmap))
        self.show()
    
    def scaleDirection(self, width, height, pixmap):
        W = pixmap.width() / width
        H = pixmap.height() / height
        print('W: ', W, 'H: ', H)
        if W < H:
            return 'width'
        else:
            return 'height'

    def list_files(self):
        self.lineEdit_clear()
        self.progressbarInit(0)
        if self.removeTempFile():
            self.selectListGraphicFiles()

    def removeTempFile(self):
        tempFile = pathlib.Path(self.getRootdir(),TEMPFILE)
        if os.path.isfile(tempFile):
            try:
                os.remove(tempFile)
                return True
            except:
                QMessageBox.about(self, "경고", "파일을 사용하고 있습니다. 파일을 닫아주세요.")
        else:
            return True            

    def filesList(self):
        return os.walk(self.getRootdir())
    
    def selectListGraphicFiles(self):
        srcTFiles = 0
        srcGFile = []
        srcOFile = []
        self.progressbarInit(len(self.filesList()))
        for path, dir, files in self.filesList():
            for file in files:
                srcTFiles += 1
                self.progressbarUpdate(srcTFiles)
                if self.suffixVerify(path, file):
                    srcGFile.append([path, file])
                else:
                    srcOFile.append([path, file])
        self.lineEdit_4.setText(str(srcTFiles))
        self.dispListWidget(srcGFile)
        self.dispListWidget_3(srcOFile)
        if sys._getframe(1).f_code.co_name == 'delAllOtherFiles':
            return srcOFile
        else:
            self.saveGraphicFileListToExcel(srcGFile)
            return srcGFile
    
    
    
    def saveGraphicFileListToExcel(self, srcGFile):
        FileName = pathlib.Path(self.getRootdir(),TEMPFILE)
        df = pd.DataFrame (srcGFile, columns = ['Source Path', 'Filename'])
        try:
            if os.path.isfile(FileName):
                os.remove(FileName)
                df.to_excel(FileName,index=False,header=False)
            else:
                df.to_excel(FileName,index=False,header=False)
        except:
            QMessageBox.about(self, "경고", "파일을 사용하고 있습니다. 파일을 닫아주세요.")
        pass
    
    def dispListWidget(self, srcGFile):
        i = 0
        for [path, file] in srcGFile:
            self.listWidget.addItem(path + '/' + file)
            i += 1
        self.lineEdit_5.setText(str(i))

    def dispListWidget_3(self, srcOFile):
        i = 0
        for [path, file] in srcOFile:
            self.listWidget_3.addItem(path + '/' + file)
            i += 1
        self.lineEdit_6.setText(str(i))

    def suffixVerify(self, path, f):
        allow_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', 'tiff'] #, '.avi','.mov', '.mp4'
        # f = pathlib.Path(path, name)  # 원본 파일
        src = pathlib.Path(path, f)
        if src.suffix.lower() in allow_exts:
            return True
        else:
            pass

    def delSelectedFile(self):
        allow_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', 'tiff', '.avi','.mov', '.mp4']
        if self.listWidget_3.currentItem():
            file = self.listWidget_3.currentItem().text()
            path, ext = os.path.splitext(file)
            if str.lower(ext) not in allow_exts:
                os.remove(file)
                self.list_files()
            else:
                QMessageBox.about(self, "경고", "그래픽이나 동영상 파일은 삭제할 수 없습니다.")

    
    def delAllOtherFiles(self):
        allow_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', 'tiff', '.avi','.mov', '.mp4']
        otherFiles = self.selectListGraphicFiles()
        for path, fileName in otherFiles:
            file, ext = os.path.splitext(fileName)
            print(ext)
            if str.lower(ext) not in allow_exts:
                f = pathlib.Path(path, fileName)
                print(f)
                print('os.remove(f)')
                os.remove(f)
            else:
                QMessageBox.about(self, "경고", "그래픽이나 동영상 파일은 삭제할 수 없습니다.")
        self.list_files()

    def getRootdir(self):
        return self.lineEdit.text()
    
    def getDestdir(self):
        return self.lineEdit_2.text()

    def delimiter_select(self):
        format = self.comboBox_2.currentText()
        if format.find('-') > 0:
            return ['-', '-', '-']
        elif format.find('_') > 0:
            return ['_', '_', '_']
        elif format.find('.') > 0:
            return ['.', '.', '.']
        elif format.find('년') > 0:
            return ['년','월','일']
        elif format.find(' ') > 0:
            return [' ', ' ', ' ']
        else :
            delimiter = ['', '', '']
            return delimiter

    def get_remark(self, path):
        if path.find('/') > 0:
            separator = '/'
        if path.find('\\') > 0:
            separator = '\\'

        sub_dir = path.split(separator)
        sub = sub_dir[-1]
        checker = re.compile(r'(19\d\d|20\d\d|\d\d)[년\-_. ]?(0[1-9]|1[012])[월\-_. ]?(0[1-9]|[12][0-9]|3[01])[일]?')
        m = checker.match(sub)
        if m and len(sub) > m.end():
            #print(sub[m.end():])
            return sub[m.end():]
        else:
            return ""        

    def takePictureTime(self, path, f):
        filename = pathlib.Path(path, f)
        try :
            with Image.open(filename) as im:
                info = im._getexif()
            # 새로운 딕셔너리 생성
            taglabel = {}
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                taglabel[decoded] = value
            s = taglabel['DateTimeOriginal']
            print(path, f, s)
            # print(s)
            timestamp = time.mktime(datetime.strptime(s, '%Y:%m:%d %H:%M:%S').timetuple())
            return timestamp
        except:
            return None
            now = datetime.now()
            timestamp = datetime.timestamp(now)

    def estimateDateFromFileName(self, fname):
        folderName = []
        D0, D1, D2 = self.delimiter_select() # delimiter
        G_files = 0
        self.progressbarInit(len(fname))
        for path, file in fname:
            #path = pathfile[0]
            #file = pathfile[1]
            G_files += 1
            self.lineEdit_5.setText(str(G_files))
            self.progressbarUpdate(G_files)
            # 기존 폴더에 설명이 있을 경우 가져옴
            remark = self.get_remark(path)
            
            # 파일 이름에 날짜 형식이 들어가 있는지 검사하여 디렉토리 생성
            checker = re.compile(r'^(19\d\d|20\d\d)[년\-_. ]?(0[1-9]|1[012])[월\-_. ]?(0[1-9]|[12][0-9]|3[01])[일]?')  
            #checker1 = re.compile(r'^(\d\d)[년\-_. ]?(0[1-9]|1[012])[월\-_. ]?(0[1-9]|[12][0-9]|3[01])[일]?')
            m = checker.search(file)
            if checker.search(file): # delimiter 종류에 따른 디렉토리 생성 
                Y = m.group(1)
                M = m.group(2)
                D = m.group(3)
                folderName.append([path, Y+D0, Y+D0+M+D1, Y+D0+M+D1+D+D2+remark, file, ''])
            else:# checker1.search(file):
                [y, ym, ymd, newFileName] = self.folderNameFromTakeMinTime(path, file, [D0, D1, D2], remark)
                folderName.append([path, y, ym, ymd, file, newFileName])

            '''    
            else: # 파일 이름에 날짜가 없을 경우 파일 생성 날짜를 유추하여 파일 디렉토리 생성
                [y, ym, ymd, newFileName] = self.folderNameFromTakeMinTime(path, file, l, remark)
                folderName.append([path, y, ym, ymd, file, newFileName])
            '''
        return folderName

    def makeNewFileName(self, f, min_time):
        dt = datetime.fromtimestamp(min_time)
        y = dt.strftime("%Y%m%d_%H%M%S")
        new_f = y+'_'+f
        return new_f
    
    def folderNameFromTakeMinTime(self, path, f, l, remark):
        # 사진찍은 날짜 가져오기
        if self.takePictureTime(path, f):
            min_time = self.takePictureTime(path, f)
            print('takePictureTime:', datetime.fromtimestamp(min_time))
        else:
            filename = os.path.join(path, f)
            T = os.stat(filename)
            #print('T.st_ctime, T.st_mtime, T.st_atime', 
            c_time = T.st_ctime
            m_time = T.st_mtime
            a_time = T.st_atime
            #c_time = os.path.getctime(filename)
            min_time = min(c_time, m_time, a_time)
            print('takeTimeFromFile: ', datetime.fromtimestamp(min_time))
        newFileName = self.makeNewFileName(f, min_time)
        # print(newFileName)
        dt = datetime.fromtimestamp(min_time)
        y = dt.strftime("%Y"+l[0])
        ym = dt.strftime("%Y"+l[0]+"%m"+l[1])
        ymd = dt.strftime("%Y"+l[0]+"%m"+l[1]+"%d"+l[2]+remark)
        return y, ym, ymd, newFileName

    def saveExcel(self, f_list, fname):
        if len(f_list) > 0:
            target_folder = self.lineEdit_2.text()
            df = pd.DataFrame (f_list, columns = ['Source Path', 'Destination Path', 'Filename'])
            FileName = pathlib.Path(target_folder, fname)
            try:
                if os.path.isfile(FileName):
                    os.remove(FileName)
                    df.to_excel(FileName,index=False,header=True)
                else:
                    df.to_excel(FileName,index=False,header=True)
            except:
                QMessageBox.about(self, "경고", "파일을 사용하고 있습니다. 파일을 닫아주세요.")
        else:
            pass

    def progressbarInit(self, length):
        self.progressBar.setMinimum(0)
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(length)

    def progressbarUpdate(self, N_files):
        self.progressBar.setValue(N_files)

    def reNameSourceFile(self, folder):
        source = pathlib.Path(folder[0], folder[4])
        newFile = pathlib.Path(folder[0], folder[5])
        if os.stat(source).st_mode == 33060: # 33060 readonly, 33206 writable
            os.chmod(source, stat.S_IWRITE)
            os.rename(source, newFile)
        else:
            os.rename(source, newFile)
        return

    def copyFile(self, folderName):
        C_files = 0
        E_files = 0
        P_files = 0
        EFile = []
        CFile = []
        target_folder = self.lineEdit_2.text()
        folder_tree = self.folder_tree()
        self.progressbarInit(len(folderName))
        for folder in folderName:
            source, y, ym, ymd, originalFileName, newFileName = folder
            if len(newFileName) > 0:
                self.reNameSourceFile(folder)
                originalFileName = newFileName
            P_files += 1
            self.progressbarUpdate(P_files)
            f = pathlib.Path(source, originalFileName)
            # 분류될 경로 생성
            t = self.makeFolder(folder_tree, target_folder, folder)
            t.mkdir(parents=True, exist_ok=True) # 파일 경로에 있는 모든 폴더를 생성함. 있으면 놔둠
            if os.path.isfile(pathlib.Path(t, originalFileName)):
                E_files += 1
                self.disp_E_files(E_files)
                self.listWidget_4.addItem(str(source) +' ' + str(t) +' ' + originalFileName)
                EFile.append([source,t, originalFileName])
            else:
                C_files += 1
                shutil.copy2(f, t) # 파일 복사 (파일 개정 시간 등 포함하여 복사를 위해 copy2 사용)pass
                self.disp_C_files(C_files)
                self.listWidget_2.addItem(str(source) +' ' + str(t) +' ' + originalFileName)
                CFile.append([source, t, originalFileName])
        self.removeTempFile()
        self.saveExcel(EFile, 'fileCopyExistingFiles.xlsx')
        self.saveExcel(CFile, 'fileCopyCopyedFiles.xlsx')
    
    def dispListWidget_2(self, srcOFile):
        i = 0
        for [path, file] in srcOFile:
            self.listWidget_2.addItem(path + '/' + file)
            i += 1
        self.lineEdit_6.setText(str(i))
    
    def disp_C_files(self, C_files):
        self.lineEdit_7.setText(str(C_files))

    def disp_E_files(self, E_files):
        self.lineEdit_9.setText(str(E_files))

    def moveFile(self, folderName):
        R_files = 0
        M_files = 0
        P_files = 0
        Rfile = []
        Mfile = []
        self.progressbarInit(len(folderName))
        target_folder = self.getDestdir()
        for folder in folderName:
            P_files += 1
            source, y, ym, ymd, oriFileName, newFileName = folder
            f = pathlib.Path(source, oriFileName) # source file 경로 및 이름
            folder_tree = self.folder_tree()
            # 분류될 경로 생성
            t = self.makeFolder(folder_tree, target_folder, folder)
            if len(newFileName) == 0:
                newFileName = oriFileName # New file name이 없을 경우 원본 파일 이름 사용
            t_file = pathlib.Path(t, newFileName) # target file 경로 및 이름 
            t.mkdir(parents=True, exist_ok=True) # 파일 경로에 있는 모든 폴더를 생성함. 있으면 놔둠
            self.progressbarUpdate(P_files)
            if os.path.isfile(t_file):
                if os.stat(f).st_mode == 33060: # 33060 readonly, 33206 writable
                    os.chmod(f, stat.S_IWRITE)
                    os.remove(f)
                else:
                    os.remove(f)
                R_files += 1
                self.lineEdit_9.setText(str(R_files))
                self.listWidget_4.addItem(str(pathlib.Path(source, oriFileName)))
                Rfile.append([source, t, oriFileName])
            else:
                M_files += 1
                shutil.move(f, t_file) # 파일 이동 후 원본 삭제
                self.lineEdit_8.setText(str(M_files))
                self.listWidget_2.addItem(str(source) + ' ' + str(t) +'/' + oriFileName)
                Mfile.append([source, t, oriFileName])
            try:
                os.rmdir(source)
            except:
                pass
        self.removeTempFile()
        self.saveExcel(Rfile, 'moveFileExistingFiles.xlsx')
        self.saveExcel(Mfile, 'moveFileMovedFiles.xlsx')
    
    def removeDir(self):
        for path, dir, f in self.filesList():
            if len(dir) == 0 and len(f) == 0 :
                if path != self.getRootdir():
                    os.rmdir(path)
        self.checkDir(self.getRootdir())
    
                
    def checkDir(self, root_dir):
        i = 0
        for path, dir, f in self.filesList():
            if len(dir) == 0 and len(f) == 0 :
                i += 1
        if i > 1:
            self.removeDir()
        else:
            QMessageBox.about(self, "폴더정리 완료", "이동 후 빈 폴더 삭제가 완료 되었습니다")
            #print("파일 정리가 완료되었습니다.")

    def makeFolder(self, folder_tree, target_folder, folder):
        if folder_tree == 'ymd':
            t = pathlib.Path(target_folder,folder[1],folder[2], folder[3])
        elif folder_tree == 'ym':
            t = pathlib.Path(target_folder,folder[1],folder[2])
        else:
            t = pathlib.Path(target_folder,folder[1])
        return t

    def folder_tree(self):
        folder_tree = self.comboBox.currentText()
        if folder_tree.find('년/월/일별로 정리') >= 0:
            folder_tree_type = 'ymd'
            return folder_tree_type
        elif folder_tree.find('년/월별로 정리') >= 0:
            folder_tree_type = 'ym'
            return folder_tree_type
        else:
            folder_tree_type = 'y'
            return folder_tree_type

    def count_clear(self):
        self.lineEdit_7.setText('0')
        self.lineEdit_8.setText('0')
        self.lineEdit_9.setText('0')
        self.listWidget_2.clear()
        self.listWidget_4.clear()

    def copy_start(self):
        if not self.checkSourceDest():
            self.count_clear()
            fl = pathlib.Path(self.getRootdir(),TEMPFILE)
            if os.path.isfile(fl):
                pathFileList = self.estimateDateFromFileName(self.openExcelFileList(fl))
            else:
                pathFileList = self.estimateDateFromFileName(self.selectListGraphicFiles())
            self.copyFile(pathFileList)
            QMessageBox.about(self, "복사 완료", "파일 복사가 완료 되었습니다")
        return

    def openExcelFileList(self,fl):
        df = pd.read_excel(fl, header=None , skiprows=0)
        print (df)
        return df.values.tolist()


    def move_start(self):
        if not self.checkSourceDest():
            self.count_clear()
            fl = pathlib.Path(self.getRootdir(),TEMPFILE)
            if os.path.isfile(fl):
                pathFileList = self.estimateDateFromFileName(self.openExcelFileList(fl))
            else:
                pathFileList = self.estimateDateFromFileName(self.selectListGraphicFiles())
            self.moveFile(pathFileList)
            QMessageBox.about(self, "이동 완료", "파일 이동이 완료 되었습니다")
            self.removeDir()
        return

    def checkSourceDest(self):
        if self.getDestdir().upper() == self.getRootdir().upper():
            QMessageBox.warning(self, "원본 폴더와 목적 폴더 동일 경고", "중요!!! 원본 폴더와 목적 폴더가 동일할 경우 모든 파일과 폴더가 삭제됩니다. 원본 폴더 또는 목적폴더를 변경하세요!!!")
            return True 

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

    
    def lineEdit_clear(self):
        self.listWidget.clear()
        self.listWidget_2.clear()
        self.listWidget_3.clear()
        self.listWidget_4.clear()
        self.lineEdit_4.clear()
        self.lineEdit_5.clear()
        self.lineEdit_6.clear()
        self.lineEdit_7.clear()
        self.lineEdit_8.clear()
        self.lineEdit_9.clear()
        self.listWidget.setAlternatingRowColors(True)

    def addListWidget(self, path, f):
        # self.addItemText = path + " " + f
        self.listWidget.addItem(path + "/" + f)
        #self.listWidget.addItem(self.addItemText)

class QImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.printer = QPrinter()
        self.scaleFactor = 0.0

        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setVisible(False)

        self.setCentralWidget(self.scrollArea)

        self.createActions()
        self.createMenus()

        self.setWindowTitle("Image Viewer")
        self.resize(800, 600)

    def open(self):
        options = QFileDialog.Options()
        # fileName = QFileDialog.getOpenFileName(self, "Open File", QDir.currentPath())
        fileName, _ = QFileDialog.getOpenFileName(self, 'QFileDialog.getOpenFileName()', '',
                                                  'Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)
        if fileName:
            image = QImage(fileName)
            if image.isNull():
                QMessageBox.information(self, "Image Viewer", "Cannot load %s." % fileName)
                return

            self.imageLabel.setPixmap(QPixmap.fromImage(image))
            self.scaleFactor = 1.0

            self.scrollArea.setVisible(True)
            self.printAct.setEnabled(True)
            self.fitToWindowAct.setEnabled(True)
            self.updateActions()

            if not self.fitToWindowAct.isChecked():
                self.imageLabel.adjustSize()

    def print_(self):
        dialog = QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = self.imageLabel.pixmap().size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.imageLabel.pixmap().rect())
            painter.drawPixmap(0, 0, self.imageLabel.pixmap())

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()

        self.updateActions()

    def about(self):
        QMessageBox.about(self, "About Image Viewer",
                          "<p>The <b>Image Viewer</b> example shows how to combine "
                          "QLabel and QScrollArea to display an image. QLabel is "
                          "typically used for displaying text, but it can also display "
                          "an image. QScrollArea provides a scrolling view around "
                          "another widget. If the child widget exceeds the size of the "
                          "frame, QScrollArea automatically provides scroll bars.</p>"
                          "<p>The example demonstrates how QLabel's ability to scale "
                          "its contents (QLabel.scaledContents), and QScrollArea's "
                          "ability to automatically resize its contents "
                          "(QScrollArea.widgetResizable), can be used to implement "
                          "zooming and scaling features.</p>"
                          "<p>In addition the example shows how to use QPainter to "
                          "print an image.</p>")

    def createActions(self):
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+O", triggered=self.open)
        self.printAct = QAction("&Print...", self, shortcut="Ctrl+P", enabled=False, triggered=self.print_)
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.zoomInAct = QAction("Zoom &In (25%)", self, shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)
        self.zoomOutAct = QAction("Zoom &Out (25%)", self, shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)
        self.normalSizeAct = QAction("&Normal Size", self, shortcut="Ctrl+S", enabled=False, triggered=self.normalSize)
        self.fitToWindowAct = QAction("&Fit to Window", self, enabled=False, checkable=True, shortcut="Ctrl+F",
                                      triggered=self.fitToWindow)
        self.aboutAct = QAction("&About", self, triggered=self.about)
        self.aboutQtAct = QAction("About &Qt", self, triggered=qApp.aboutQt)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))



if __name__ == "__main__":
    app = QApplication(sys.argv)
    elWindow = ElWindow()
    elWindow.show()
    app.exec_()