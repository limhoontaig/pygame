import sys
import os
import stat
import pathlib
import pandas as pd
from PyQt5.QtCore import Qt, pyqtSlot, QObject, pyqtSignal, QStringListModel, QDate, QSize
from PyQt5 import uic
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter, QBrush
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QAction, \
    qApp, QFileDialog, QApplication, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox

from datetime import datetime
from datetime import date
import re
from time import time
import time
import shutil
from PIL import Image
from PIL.ExifTags import TAGS
import pandas as pd
import numpy as np
import mysql
import mysql.connector
import math
from threading import Event, Timer
import cv2

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
    'D:\\개인자료\\개인 사진\\2004년\\041106 한수원 신불산행 사진',
    'C:\\사진'
    ]
TEMPFILE = 'TEMP_EXCEL_FileList.xlsx'

ALLOW_GRAPHIC = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', 'tiff']
ALLOW_MEDIA = ['.avi','.mov', '.mp4']
ALLOW_EXTS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', 'tiff', '.avi','.mov', '.mp4']

class cvWindow():
    def imShow(self, f):
        print(f)
        img = cv2.imread(f, cv2.IMREAD_COLOR)
        if img is None:
            print("Not Load the Image")
            return
        cv2.imshow('show', img)
        cv2.waitKey(10)
        cv2.destroyAllWindows()


class ElWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.LE = LE
        self.TEMPFILE = TEMPFILE
        self.setupUi(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.lineEdit.setText(LE[0])
        self.lineEdit_2.setText(LE[1])
        issued = '프로그램 작성 : 임훈택 Rev 0 '+ yyyymmdd + ' Issued'
        self.label.setText(issued)
        
        self.disablePushButton()
        self.disablePBCopyMove()
        self.checkBox_3.setCheckState(2)
        self.checkBox_4.setCheckState(2)
        #self.checkBox_5.setCheckState(2)
        self.checkBox_6.setChecked(2)

        self.scaleFactor = 0.0
        self.label_8 = QLabel()#.setText('Image Viewer')
        self.label_8.setBackgroundRole(QPalette.Base)
        self.label_8.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label_8.setScaledContents(True)

        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.label_8)
        self.scrollArea.setVisible(True)

        self.scrollArea.mouseMoveEvent = self.mouseMoveEvent
        self.scrollArea.mousePressEvent = self.mousePressEvent
        self.scrollArea.mouseReleaseEvent = self.mouseReleaseEvent

        self.label_8.setCursor(Qt.OpenHandCursor)

        self.pushButton.clicked.connect(self.add_file)
        self.pushButton_2.clicked.connect(self.add_file)
        self.pushButton_3.clicked.connect(self.copy_start)
        self.pushButton_4.clicked.connect(self.move_start)
        self.pushButton_5.clicked.connect(self.list_files) 
        self.pushButton_6.clicked.connect(self.zoomIn) # Zoom in
        self.pushButton_7.clicked.connect(self.zoomOut) # Zoom out
        self.pushButton_9.clicked.connect(self.fitToScaledSize) # Fit to Scaled Size
        #self.pushButton_10.clicked.connect(self.slideStop) # Slide stop
        self.pushButton_8.clicked.connect(self.slideShow) # Slide Show 
        self.pushButton_11.clicked.connect(self.normalSize) # Fit to Normal size 
        self.pushButton_12.clicked.connect(self.delSelectedFile) # Fit to Normal size 
        self.pushButton_13.clicked.connect(self.delAllOtherFiles) # Fit to Normal size 
        self.pushButton_16.clicked.connect(self.delSelectedItems) # delete select items
        self.pushButton_17.clicked.connect(self.delAllItems) # delete all tablewidget items
        self.pushButton_18.clicked.connect(self.renameFolder) # Fit to Normal size
        #self.pushButton_19.clicked.connect(self.selectSQL) # 검색조건에 따른 sql문 선택
        self.pushButton_20.clicked.connect(self.searchData) # 선택기간 DB 검색 
        self.tableWidget.cellClicked.connect(self.set_label)
        self.listWidget.itemClicked.connect(self.makePixmap)
        self.checkBox_2.stateChanged.connect(self.fitToWindow)
        self.checkBox_6.stateChanged.connect(self.fitToScaledSize)
        # self.lineEdit.textChanged.connect(self.enablePBCopyMove)

    def slideShow(self):
        row = self.tableWidget.currentRow()
        rows = self.tableWidget.rowCount()
        if row == -1:
            QMessageBox.about(self, "파일 선택 요망", "테이블 상의 파일을 선택하신 후 Slide Show가 가능합니다. 파일선택후 재실행 해주세요.")
            return
        for i in range(row, rows):
            self.tableWidget.setCurrentCell(i, 1)
            if self.checkBox.isChecked():
                break
            #if  
            #self.set_label(i, 1)
            file = self.tableWidget.item(i, 2).text()
            path = self.tableWidget.item(i, 4).text()
            fileName = str(pathlib.Path(path, file))
            self.qImageViewer(fileName)
            # 별도의 창을 띄워 슬리이드 보이기 하려면 아래 주석을 해제 하면 됨
            '''
            # gif 처리
            if str(fileName).lower().endswith('.gif'):
                gif = cv2.VideoCapture(fileName)
                ret, frame = gif.read()  # ret=True if it finds a frame else False.
                if ret:
                    img = frame
            else:
                img_array = np.fromfile(fileName, np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            #cv2.waitKey(100)
            width, height, dim = img.shape
            print(width, height, dim, fileName)
            if width > height:
                fx_x = 640 / width
            else:
                fx_x = 640 / height
            #dst = cv2.resize(img, dsize=(640, 480), interpolation=cv2.INTER_AREA)
            dst2 = cv2.resize(img, dsize=(0, 0), fx=fx_x, fy=fx_x, interpolation=cv2.INTER_LINEAR)
            #cv2.imshow("src", src)
            #cv2.imshow("dst", dst)
            #cv2.imshow("Image Slide Show", dst2)
            '''
            cv2.waitKey(1500)
            #cv2.destroyAllWindows()

    def mousePressEvent(self, event):
        self.pressed = True
        self.label_8.setCursor(Qt.ClosedHandCursor)
        self.initialPosX = self.scrollArea.horizontalScrollBar().value() + event.pos().x()
        self.initialPosY = self.scrollArea.verticalScrollBar().value() + event.pos().y()

    def mouseReleaseEvent(self, event):
        self.pressed = False
        self.label_8.setCursor(Qt.OpenHandCursor)
        self.initialPosX = self.scrollArea.horizontalScrollBar().value()
        self.initialPosY = self.scrollArea.verticalScrollBar().value()

    def mouseMoveEvent(self, event):
        if self.pressed:
            self.scrollArea.horizontalScrollBar().setValue(self.initialPosX - event.pos().x())
            self.scrollArea.verticalScrollBar().setValue(self.initialPosY - event.pos().y())
    
    def delAllItems(self):
        rows = self.tableWidget.rowCount()
        reply = QMessageBox.question(self, "파일 삭제 확인", "테이블 상의 모든 파일 " + str(rows) +"개 사진을 삭제하시겠습니까? 사진을 삭제하면 복구가 불가능합니다.")
        if reply != QMessageBox.Yes:
            return
        j = 0
        for i in range(0, rows):
            fileName = self.tableWidget.item(i, 1).text()
            result = self.selectDB(fileName)
            filePath = result['pictureFileDestDir'] # dict format read data
            file = pathlib.Path(filePath, fileName)
            self.deleteDB([fileName])
            try:
                os.remove(file)
            except:
                j += 1
                if j < 3:
                    QMessageBox.about(self, "경고", "파일이 없습니다. 파일을 확인해 주세요.")
                    pass
                else:
                    pass
        try:
            self.removeDir()
        except:
            pass
        self.searchData()

    def delSelectedItems(self):
        selectedList = []
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            if currentQTableWidgetItem.column() == 1:
                fileName = currentQTableWidgetItem.text()
                result = self.selectDB(fileName)
                filePath = result['pictureFileDestDir'] # dict format read data
                file = pathlib.Path(filePath, fileName)
                selectedList.append([fileName, filePath, file])
        reply = QMessageBox.question(self, "파일 삭제 확인", "선택하신 파일 " + str(len(selectedList)) +"개 사진을 삭제하시겠습니까?")
        if reply != QMessageBox.Yes:
            return
        
        for fileName, filePath, file in selectedList:
            self.deleteDB([fileName])
            os.remove(file)
        self.searchData()
        
    def deleteDB(self, newFile):
        conn = self.connDB()
        cursor = conn.cursor(dictionary=True)
        sql = "DELETE FROM mypicturefiles WHERE pictureFileName = %s"
        val = (newFile)
        cursor.execute(sql, val)
        conn.commit()
        conn.close()
        return

    def set_label(self, row, column):
        print('set_label(self, row, column): ', row, column)
        column = 0
        file = (self.tableWidget.item(row, 2).text())
        path = (self.tableWidget.item(row, 4).text())
        remark = (self.tableWidget.item(row, 3).text())
        fileName = str(pathlib.Path(path, file))
        print('set_label(self, row, column):', fileName)
        self.lineEdit_13.setText(remark)
        self.lineEdit_14.setText(remark)
        self.lineEdit_3.setText(file)
        self.lineEdit_11.setText(path)
        self.lineEdit_15.setText(str(row))
        if self.checkBox_2.isChecked():
            self.disablePushButton()
        else:
            self.enablePushButton()
        if self.checkBox_6.isChecked():
            self.fitToScaledSize()
        else:
            self.qImageViewer(fileName)
        
    @pyqtSlot()
    def searchData(self):
        if self.checkBox_5.isChecked():
            from_date = '1970-01-01'
            to_date = QDate.currentDate().toString(Qt.ISODate)
        else:
            from_date = self.dateEdit.text()
            to_date = self.dateEdit_2.text()
        fileName, activityName = self.selectSQL()
        results = self.searchPeriod(from_date, to_date, fileName, activityName)
        data = []
        self.tableWidget.clear()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setSortingEnabled(True)
        for result in results:
            data.append([str(result['Number']), result['pictureFileName'], result['remark'], result['pictureFileDestDir'], str(result['TakeTime']), result['fileSize']])
        self.set_tableWidget(data)

    def selectSQL(self):
        if self.checkBox_3.isChecked():
            if self.checkBox_4.isChecked():
                if len(self.lineEdit_12.text()) == 0:
                    fileName = '%%'
                else:
                    fileName = '%' + self.lineEdit_12.text() + '%'
                if len(self.lineEdit_16.text()) == 0:
                    activityName = '%%'
                else:
                    activityName = '%' + self.lineEdit_16.text() + '%'
            else:
                if len(self.lineEdit_12.text()) == 0:
                    fileName = '%%'
                else:
                    fileName = '%' + self.lineEdit_12.text() + '%'
                if len(self.lineEdit_16.text()) == 0:
                    activityName = '%%'
                else:
                    activityName = self.lineEdit_16.text()
        else:
            if self.checkBox_4.isChecked():
                if len(self.lineEdit_12.text()) == 0:
                    fileName = '%%'
                else:
                    fileName = self.lineEdit_12.text()
                if len(self.lineEdit_16.text()) == 0:
                    activityName = '%%'
                else:
                    activityName = '%' + self.lineEdit_16.text() + '%'
            else:
                if len(self.lineEdit_12.text()) == 0:
                    fileName = '%%'
                else:
                    fileName = self.lineEdit_12.text()
                if len(self.lineEdit_16.text()) == 0:
                    activityName = '%%'
                else:
                    activityName = self.lineEdit_16.text()
        return fileName, activityName

    def searchPeriod(self, fromDate, toDate, fileName, activityName):
        conn = self.connDB()
        cursor = conn.cursor(dictionary=True)
        sql = "select * from mypicturefiles where DATE(TakeTime) between %s and %s and \
            pictureFileName like %s and remark like %s;"
        val = (fromDate, toDate, fileName, activityName)
        cursor.execute(sql, val)
        result = cursor.fetchall()
        conn.close()
        return result
    
    def set_tableWidget(self,data):
        
        HEADERS = ['C', 'Number', 'File Name', 'Remark', 'Directory', 'Take Time', 'File Size']
        self.tableWidget.setColumnCount(len(HEADERS))
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setHorizontalHeaderLabels(HEADERS)#.split(";"))
        '''
        hitem = self.tableWidget.horizontalHeaderItem(1)
        if hitem is not None:
            hitem.setBackground(QBrush(Qt.cyan))
        '''
        rowCount = len(data)
        self.tableWidget.setRowCount(rowCount)
        for idx, (number, fileName, remark, directory, takeTime, fileSize) in enumerate(data):
            item = MyQTableWidgetItemCheckBox()
            self.tableWidget.setItem(idx, 0, item)
            chbox = MyCheckBox(item)
            self.tableWidget.setCellWidget(idx, 0, chbox)
            chbox.stateChanged.connect(self.__checkbox_change)
            self.tableWidget.setItem(idx, 1, QTableWidgetItem(number))
            self.tableWidget.setItem(idx, 2, QTableWidgetItem(fileName))
            self.tableWidget.setItem(idx, 3, QTableWidgetItem(remark))
            self.tableWidget.setItem(idx, 4, QTableWidgetItem(directory))
            self.tableWidget.setItem(idx, 5, QTableWidgetItem(takeTime))
            self.tableWidget.setItem(idx, 6, QTableWidgetItem(fileSize))
        self.tableWidget.setSortingEnabled(False)

        '''#self.table.setColumnWidth(2, 50)
        ckbox = QCheckBox()
        self.table.setCellWidget(0, 2, ckbox)
        ckbox2 = QCheckBox('me')
        self.table.setCellWidget(1, 2, ckbox2)
        
        c = 0
        for list in data:
            self.tableWidget.setColumnCount(len(list))
            for i in list:
                self.tableWidget.setItem(0, c, QTableWidgetItem(i))
                c = c+1
        '''
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.setColumnWidth(0, 15)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        hheader = self.tableWidget.horizontalHeader()
        hheader.sectionClicked.connect(self._horizontal_header_clicked)


    def __checkbox_change(self, checkvalue):
        # print("check change... ", checkvalue)
        chbox = self.sender()  # signal을 보낸 MyCheckBox instance
        print("checkbox sender row = ", chbox.get_row())

    def _cellclicked(self, row, col):
        print("_cellclicked... ", row, col)

    def _horizontal_header_clicked(self, idx):
        """
        컬럼 헤더 click 시에만, 정렬하고, 다시 정렬기능 off 시킴
         -- 정렬기능 on 시켜놓으면, 값 바뀌면 바로 자동으로 data 순서 정렬되어 바뀌어 헷갈린다..
        :param idx -->  horizontalheader index; 0, 1, 2,...
        :return:
        """
        # print("hedder2.. ", idx)
        self.tableWidget.setSortingEnabled(True)  # 정렬기능 on
        # time.sleep(0.2)
        self.tableWidget.setSortingEnabled(False)  # 정렬기능 off

    def table_display(self):
        header = self.tableWidget.horizontalHeader()
        twidth = header.width()
        width = []
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            width.append(header.sectionSize(column))
        
        wfactor = int(twidth / sum(width))
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            header.resizeSection(column, width[column]*wfactor)
        self.tableWidget.scrollToBottom


    def disablePBCopyMove(self):
        self.pushButton_3.setDisabled(True)
        self.pushButton_4.setDisabled(True)


    def enablePBCopyMove(self):
        self.pushButton_3.setEnabled(True)
        self.pushButton_4.setEnabled(True)

    def disablePushButton(self):
        self.pushButton_6.setDisabled(True) # Zoom in
        self.pushButton_7.setDisabled(True) # Zoom out
        self.pushButton_9.setDisabled(True) # Fit to Scaled Size
        #self.pushButton_10.setDisabled(True) # Fit to Height 
        self.pushButton_11.setDisabled(True) # Fit to Normal size
        self.checkBox_6.setDisabled(True) #  Scaled

    def enablePushButton(self):
        self.pushButton_6.setEnabled(True) # Zoom in
        self.pushButton_7.setEnabled(True) # Zoom out
        #self.pushButton_8.setEnabled(True) # Fit to Label
        self.pushButton_9.setEnabled(True) # Fit to Scaled Size
        #self.pushButton_10.setEnabled(True) # Fit to Height 
        self.pushButton_11.setEnabled(True) # Fit to Normal size
        self.checkBox_6.setEnabled(True) # Fit Scaled

    def fitToWidth(self):
        #pixmap = self.makePixmap()
        #self.label_8.resize(pixmap.scaledToWidth(self.label_8.pixmap.size()))
        #pixmap = pixmap.scaledToWidth(660)
        #self.label_8.pixmap.setToWidth()
        pass

    def fitToHeight(self):
        #pixmap = self.makePixmap()
        #self.label_8.resize(pixmap.scaledToHeight(self.label_8.pixmap.size()))
        #pixmap = pixmap.scaledToHeight(460)
        pass

    def normalSize(self):
        self.label_8.adjustSize()
        self.scaleFactor = 1.0

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.label_8.resize(self.scaleFactor * self.label_8.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)
        
        self.pushButton_6.setEnabled(self.scaleFactor < 3.0)
        self.pushButton_7.setEnabled(self.scaleFactor > 0.1)
    
    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))

    def makePixmap(self):    
        file = self.listWidget.currentItem().text()
        path, f = os.path.split(file)
        self.lineEdit_3.setText(self.get_remark(path))
        self.qImageViewer(file)
        
    def qImageViewer(self, f):
        print('qImageViewer fileName: ', f)
        if f:
            pixmap = QPixmap(f)
            if pixmap == 'Null':
                QMessageBox.information(self, "Image Viewer", "Cannot Load %s." % f)
                return
            self.label_8.setPixmap(QPixmap(pixmap))
            self.scaleFactor = 1.0
            self.scrollArea.setVisible(True)
            if not self.checkBox_2.isChecked():
                self.label_8.adjustSize()
            if self.checkBox_6.isChecked():
                width = 671
                height = 481
                if self.scaleDirection(width, height, pixmap) == 'width':
                    pixmap = pixmap.scaledToWidth(width)
                else:
                    pixmap = pixmap.scaledToHeight(height)
                self.label_8.setPixmap(QPixmap(pixmap))
                self.label_8.adjustSize()
            
        
    def fitToScaledSize(self):
        row = self.tableWidget.currentRow()
        self.fitToScaledSizeShow(row)
    
    def fitToScaledSizeShow(self, row):
        self.fitToWindow()
        print('row', row)
        width = 671
        height = 481
        file = self.tableWidget.item(row, 2).text()
        path = self.tableWidget.item(row, 4).text()
        
        f = str(pathlib.Path(path, file))
        if self.checkBox_6.isChecked():
            pixmap = QPixmap(f)
            
            if self.scaleDirection(width, height, pixmap) == 'width':
                pixmap = pixmap.scaledToWidth(width)
            else:
                pixmap = pixmap.scaledToHeight(height)
            self.label_8.setPixmap(QPixmap(pixmap))
            self.label_8.adjustSize()
            return
        else:
            self.qImageViewer(f)
            return
        
    def fitToWindow(self):
        fitToWindow = self.checkBox_2.isChecked()
        if fitToWindow:
            self.disablePushButton()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.enablePushButton()
            self.normalSize()
    
    def scaleDirection(self, width, height, pixmap):
        W = pixmap.width() / width
        H = pixmap.height() / height
        if W > H:
            return 'width'
        else:
            return 'height'        

    def list_files(self):
        self.lineEdit_clear()
        self.progressbarInit(0)
        if self.removeTempFile():
            self.selectListGraphicFiles()
        self.enablePBCopyMove()

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
        if os.path.isdir(self.getRootdir()) == False:
            QMessageBox.about(self, "경고", "선택된 디렉터리가 없습니다. 다시 선택해 주세요.")
            return
        return os.walk(self.getRootdir())
    
    def selectListGraphicFiles(self):
        srcTFiles = 0
        srcGFile = []
        srcOFile = []
        if self.filesList() == None:
            return
        for path, dir, files in self.filesList():
            self.progressbarInit(len(files))
            for file in files:
                srcTFiles += 1
                self.lineEdit_4.setText(str(srcTFiles))
                self.progressbarUpdate(srcTFiles)
                if self.suffixVerify(path, file):
                    srcGFile.append([path, file])
                else:
                    srcOFile.append([path, file])
            cv2.waitKey(1)
        self.dispListWidget(srcGFile)
        self.dispListWidget_3(srcOFile)
        if sys._getframe(1).f_code.co_name == 'delAllOtherFiles':
            return srcOFile
        else:
            return srcGFile

    def convert_size(self, f):
        size_bytes = os.path.getsize(f)
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 4)
        return "%s %s" % (s, size_name[i])
    
    def connDB(self):
        conn = mysql.connector.connect(
        host='localhost', 
        port='3306', 
        database='mypictures', 
        user='root', 
        password='1234'
        )
        return conn
    
    def fileToDB(self):
        target_folder = self.lineEdit_2.text()
        folder_tree = self.folder_tree()
        Graphicfiles = self.estimateDateFromFileName(self.selectListGraphicFiles())
        for folder in Graphicfiles:
            srcPath, y, ym, ymd, originalFileName, newFileName = folder
            f = pathlib.Path(srcPath, originalFileName)
            destPath = self.makeFolder(folder_tree, target_folder, folder)
            destPath.mkdir(parents=True, exist_ok=True)
            remark = self.get_remark(srcPath)
            file_size = self.convert_size(f)
            _, tt = self.takePictureTime(srcPath, originalFileName)
            exist = self.selectDB(str(newFileName)) # newfileName으로 검색하여야 함
            pathExist = self.selectPathDB(newFileName, str(destPath))
            if not exist:
                self.insertDB(newFileName, str(destPath), originalFileName, srcPath, tt, remark, file_size)
            elif pathExist:
                pass
            else:
                dupliExist = self.selectDupliDB(originalFileName, srcPath)
                if not dupliExist:
                    self.insertDupliDB(originalFileName, srcPath, destPath, remark)

    def insertDupliDB(self, f, srcDir, destDir, d):
        conn = self.connDB()
        cursor = conn.cursor(dictionary=True)
        sql = "insert into duplicatedpicturefiles (duPicFileName, srcDir, destDir, action) \
        values (%s, %s, %s, %s)"
        val = (f, str(srcDir), str(destDir), 'Delete')
        cursor.execute(sql, val)
        conn.commit()
        conn.close()
        return
    
    def insertDB(self, newFile, destDir, oldFile, srcDir, TakeTime, remark, fileSize):
        conn = self.connDB()
        cursor = conn.cursor(dictionary=True)
        sql = "insert into mypicturefiles (pictureFileName, pictureFileDestDir, \
            pictureFileOldName, pictureFileSrcDir, TakeTime, remark, fileSize) \
            values (%s, %s, %s, %s, %s, %s, %s)"
        val = (newFile, destDir, oldFile, srcDir, TakeTime, remark, fileSize)
        cursor.execute(sql, val)
        conn.commit()
        conn.close()
        return
    
    def selectDupliDB(self, file, path):
        conn = self.connDB()
        cursor = conn.cursor(dictionary=True)
        sql = "select duPicFileName from duplicatedpicturefiles \
            where duPicFileName = %s and srcDir = %s;"
        val = (file, path)
        cursor.execute(sql, val)
        result = cursor.fetchall()
        conn.close()
        return result
    
    def selectPathDB(self, file, path):
        conn = self.connDB()
        cursor = conn.cursor(dictionary=True)
        sql = "select pictureFileOldName from mypicturefiles \
            where pictureFileSrcDir = %s and pictureFileOldName = %s;"
        val = (path, file)
        cursor.execute(sql, val)
        result = cursor.fetchone()
        conn.close()
        return result
    
    def selectDB(self, f):
        conn = self.connDB()
        cursor = conn.cursor(dictionary=True)
        sql = "select pictureFileDestDir from mypicturefiles where pictureFileName = %s;"
        val = ([f])
        cursor.execute(sql, val)
        result = cursor.fetchone()
        conn.close()
        return result
    
    def renameFolder(self):
        if self.lineEdit_3.text() == '':
            QMessageBox.about(self, "경고", "파일이 선택되지 않았습니다. 파일을 선택해 주세요.")
            return
        #index_row = int(self.lineEdit_15.text())
        remark = self.lineEdit_13.text()
        new_remark = self.lineEdit_14.text()
        #file = self.lineEdit_3.text()
        Path = self.lineEdit_11.text()
        if remark == new_remark:
            QMessageBox.about(self, "경고", "변경할 내용이 없습니다. 내용을 변경 후 다시 실행해 주세요.")
            return
        head, tail = os.path.split(Path)
        if len(remark) != 0:
            new_tail = tail.replace(remark, new_remark)
        else:
            new_tail = tail + '_' + new_remark
        path = os.path.join(Path,)
        newDir = pathlib.Path(head, new_tail)
        self.updateRemarkDB(str(newDir), new_remark, self.lineEdit_11.text())
        os.rename(path, newDir)
        self.searchData()
        self.resetClickedData()
        
    def resetClickedData(self):
        self.lineEdit_15.setText('')
        self.lineEdit_13.setText('')
        self.lineEdit_14.setText('')
        self.lineEdit_3.setText('')
        self.lineEdit_11.setText('')

    def updateRemarkDB(self, newDir, remark, path):
        conn = self.connDB()
        cursor = conn.cursor(dictionary=True)
        sql = 'UPDATE mypicturefiles SET pictureFileDestDir = %s, remark = %s WHERE pictureFileDestDir = %s;'
        val = (str(newDir), remark, str(path))
        cursor.execute(sql, val)
        conn.commit()
        cursor.close()
        conn.close()
        return
    
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
        for path, file in srcGFile:
            self.listWidget.addItem(str(pathlib.Path(path, file)))
            i += 1
        self.lineEdit_5.setText(str(i))

    def dispListWidget_3(self, srcOFile):
        i = 0
        for path, file in srcOFile:
            self.listWidget_3.addItem(str(pathlib.Path(path, file)))
            i += 1
        self.lineEdit_6.setText(str(i))

    def suffixVerify(self, path, f):
        src = pathlib.Path(path, f)
        if src.suffix.lower() in ALLOW_GRAPHIC:
            return True
        elif src.suffix.lower() in ALLOW_MEDIA:
            if self.checkReMatch(f):
                return True
        else:
            return False

    def delSelectedFile(self):
        if self.listWidget_3.currentItem():
            file = self.listWidget_3.currentItem().text()
            path, ext = os.path.splitext(file)
            if str.lower(ext) not in ALLOW_EXTS:
                os.remove(file)
                self.list_files()
            else:
                QMessageBox.about(self, "경고", "그래픽이나 동영상 파일은 삭제할 수 없습니다.")
    
    def delAllOtherFiles(self):
        otherFiles = self.selectListGraphicFiles()
        for path, fileName in otherFiles:
            file, ext = os.path.splitext(fileName)
            if str.lower(ext) not in ALLOW_EXTS:
                f = pathlib.Path(path, fileName)
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

    def checkReMatch(self, path):# 처음부터 맞는지 확인하는삭
        checker = re.compile(r'(19\d\d|20\d\d|\d\d)[년\-_.: ]?(0[1-9]|1[012])[월\-_.: ]?(0[1-9]|[12][0-9]|3[01])[일]?[_ ]([01][0-9]|2[0-3])?[시\-_.: ]?[[0-5][0-9]]?[분\-_.: ]?[[0-5][0-9]]?[초]?')
        return checker.match(path)
    
    def checkReSearch(self, path):# 중간부터라도 있는지 확인하는식
        checker = re.compile(r'(19\d\d|20\d\d|\d\d)[년\-_.: ]?(0[1-9]|1[012])[월\-_.: ]?(0[1-9]|[12][0-9]|3[01])[일]?[_ ]([01][0-9]|2[0-3])?[시\-_.: ]?[[0-5][0-9]]?[분\-_.: ]?[[0-5][0-9]]?[초]?')
        return checker.search(path)
    
    def checkReMatchYMD(self, path):# 처음부터 맞는지 확인하는삭
        checker = re.compile(r'(19\d\d|20\d\d|\d\d)[년\-_.: ]?(0[1-9]|1[012])[월\-_.: ]?(0[1-9]|[12][0-9]|3[01])[일]?')
        return checker.match(path)
    
    def checkReSearchYMD(self, path):#중간에라도 맞는 식이 있는지 확인
        checker = re.compile(r'(19\d\d|20\d\d|\d\d)[년\-_.: ]?(0[1-9]|1[012])[월\-_.: ]?(0[1-9]|[12][0-9]|3[01])[일]?')
        return checker.search(path)
    
    def get_remark(self, path):
        lastDir = os.path.basename(path)
        m = self.checkReMatchYMD(lastDir)
        if (m and len(lastDir) > m.end()):
            if (lastDir[m.end()] == ' ' or lastDir[m.end()] == '_' or lastDir[m.end()] == '-'):
                return lastDir[m.end()+1:]
            else:
                return lastDir[m.end():]
        else:
            return ""        

    def takePictureTimeStrf(self, path, f):
        s = self.getexif(path, f)
        return self.getexif(path, f)
    
    def takePictureTimestamp(self, path, f):
        if self.getexif(path, f):
            s = self.getexif(path, f)
            timestamp = time.mktime(datetime.strptime(s, '%Y:%m:%d %H:%M:%S').timetuple())
            return timestamp
        else:
            return None

    def getexif(self, path, f):
        filename = pathlib.Path(path, f)
        try :
            with Image.open(filename) as im:
                info = im._getexif()
            # 새로운 딕셔너리 생성
            taglabel = {}
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                taglabel[decoded] = value
            if self.checkReMatch(taglabel['DateTimeOriginal']):
                s = taglabel['DateTimeOriginal']
                return s
            elif self.checkReMatch(taglabel['DateTimeDigitized']):
                s = taglabel['DateTimeDigitized']
                return s
            elif self.checkReMatch(taglabel['DateTime']):
                s = taglabel['DateTime']
                return s
            else:
                return None
        except:
            return None

    def estimateDateFromFileName(self, fname):
        folderName = []
        D0, D1, D2 = self.delimiter_select() # delimiter
        G_files = 0
        self.progressbarInit(len(fname))
        for path, file in fname:
            G_files += 1
            self.lineEdit_5.setText(str(G_files))
            self.progressbarUpdate(G_files)
            # 기존 폴더에 설명이 있을 경우 가져옴
            remark = self.get_remark(path)
            # 파일 이름에 날짜 형식이 들어가 있는지 검사하여 디렉토리 생성
            m = self.checkReSearch(file)
            if m: # delimiter 종류에 따른 디렉토리 생성
                if m.end() == 15:
                    Y = m.group(1)
                    y, ym, ymd, newFileName = self.folderNameFromTakeMinTime(path, file, [D0, D1, D2], remark)
                    M = m.group(2)
                    D = m.group(3)
                    if len(remark) != 0:
                        folderName.append([path, Y+D0, Y+D0+M+D1, Y+D0+M+D1+D+D2+'_'+remark, file, file])
                    else:
                        folderName.append([path, Y+D0, Y+D0+M+D1, Y+D0+M+D1+D+D2+remark, file, file])

                else:
                    y, ym, ymd, newFileName = self.folderNameFromTakeMinTime(path, file, [D0, D1, D2], remark)
                    folderName.append([path, y, ym, ymd, file, newFileName])
            else:# checker1.search(file):
                y, ym, ymd, newFileName = self.folderNameFromTakeMinTime(path, file, [D0, D1, D2], remark)
                folderName.append([path, y, ym, ymd, file, newFileName])
            cv2.waitKey(10)
        return folderName

    def makeNewFileName(self, f, min_time):
        original = f
        dt = datetime.fromtimestamp(min_time)
        y = dt.strftime("%Y%m%d_%H%M%S")
        p =self.checkReMatch(f)
        if p != None:
            if p.end() == 15:
                new_f = f
                return new_f
        if f[0] == '_': # file 명이 _로 시작하면 _ 제외
            f = f[1:]
        n = self.checkReSearch(f)
        if n != None:
            if n.start() == 0:
                f = f[n.end():]
            else:
                f = f[:n.start()] + f[n.end():]
                if f[0] == '_' or f[0] == ' ': # file 명이 _로 시작하면 _ 제외
                    f = f[1:]
            new_f = y + '_' + f
            return new_f
        m = self.checkReSearchYMD(f)
        if m != None:
            if m.start() == 0:
                f = f[m.end():]
            else:
                f = f[:m.start()] + f[m.end():]
                if (f[0] == ' ' or f[0] == '_'): # file 명이 _로 시작하면 _ 제외
                    f = f[1:]
                if f[0] == 'P':
                    f = original
            new_f = y + '_' + f
            return new_f
        new_f = y + '_' + f
        return new_f
    
    def folderNameFromTakeMinTime(self, path, f, l, remark):
        # 사진찍은 날짜 가져오기
        if self.takePictureTimestamp(path, f):
            min_time = self.takePictureTimestamp(path, f)
        else:
            min_time = self.get_min_time(path, f)
        newFileName = self.makeNewFileName(f, min_time)
        dt = datetime.fromtimestamp(min_time)
        y = dt.strftime("%Y"+l[0])
        ym = dt.strftime("%Y"+l[0]+"%m"+l[1])
        if len(remark) != 0:
            ymd = dt.strftime("%Y"+l[0]+"%m"+l[1]+"%d"+l[2] +'_'+ remark)
        else:
            ymd = dt.strftime("%Y"+l[0]+"%m"+l[1]+"%d"+l[2] + remark)
        return y, ym, ymd, newFileName

    def get_min_time(delf, path, f):
        filename = os.path.join(path, f)
        T = os.stat(filename)
        c_time = T.st_ctime
        m_time = T.st_mtime
        a_time = T.st_atime
        return min(c_time, m_time, a_time)

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
    def getVariables(self, srcPath, f, originalFileName):
        remark = self.get_remark(srcPath)
        fileSize = self.convert_size(f)
        if self.takePictureTimeStrf(srcPath, originalFileName):
            takeTime = self.takePictureTimeStrf(srcPath, originalFileName)
        else:
            min_time = self.get_min_time(srcPath, originalFileName)
            dt = datetime.fromtimestamp(min_time)
            takeTime = dt.strftime('%Y:%m:%d %H:%M:%S')
        return remark, fileSize, takeTime


    def copyFile(self, pathFileList):
        C_files = 0
        E_files = 0
        I_files = 0
        P_files = 0
        EFile = []
        CFile = []
        target_folder = self.lineEdit_2.text()
        folder_tree = self.folder_tree()
        self.progressbarInit(len(pathFileList))
        for folder in pathFileList:
            srcPath, y, ym, ymd, originalFileName, newFileName = folder
            f = pathlib.Path(srcPath, originalFileName)
            remark, fileSize, takeTime = self.getVariables(srcPath, f, originalFileName)
            P_files += 1
            self.progressbarUpdate(P_files)
            # 분류될 경로 생성
            destPath = self.makeFolder(folder_tree, target_folder, folder)
            destPath.mkdir(parents=True, exist_ok=True) # 파일 경로에 있는 모든 폴더를 생성함. 있으면 놔둠
            destFile = pathlib.Path(destPath, newFileName)
            if not self.selectDB(newFileName):
                self.insertDB(newFileName, str(destPath), originalFileName, srcPath, takeTime, remark, fileSize)
                C_files += 1
                #shutil.copy2(f, destFile) # 파일 복사 (파일 개정 시간 등 포함하여 복사를 위해 copy2 사용)pass
                self.disp_C_files(C_files)
                self.listWidget_2.addItem(str(srcPath) +' ' + str(destPath) +' ' + originalFileName)
                CFile.append([originalFileName, srcPath, destPath])
            elif self.selectPathDB(originalFileName, srcPath):
                I_files += 1
                self.disp_I_files(I_files)
                pass
            else:
                if not self.selectDupliDB(originalFileName, srcPath):
                    self.insertDupliDB(originalFileName, srcPath, destPath, 'Delete')
                    E_files += 1
                    self.disp_E_files(E_files)
                    self.listWidget_4.addItem(originalFileName + ' ' + str(srcPath) +' ' + str(destPath))
                    EFile.append([originalFileName, srcPath, destPath])
            cv2.waitKey(10)
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
    
    def disp_I_files(self, I_files):
        self.lineEdit_10.setText(str(I_files))

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
            srcPath, y, ym, ymd, oriFileName, newFileName = folder
            f = pathlib.Path(srcPath, oriFileName) # source file 경로 및 이름
            folder_tree = self.folder_tree()
            # 분류될 경로 생성
            destPath = self.makeFolder(folder_tree, target_folder, folder)
            remark, fileSize, takeTime = self.getVariables(srcPath, f, oriFileName)
            if len(newFileName) == 0:
                newFileName = oriFileName # New file name이 없을 경우 원본 파일 이름 사용
            t_file = pathlib.Path(destPath, newFileName) # target file 경로 및 이름 
            destPath.mkdir(parents=True, exist_ok=True) # 파일 경로에 있는 모든 폴더를 생성함. 있으면 놔둠
            self.progressbarUpdate(P_files)
            if not self.selectDB(newFileName):
                self.insertDB(newFileName, str(destPath), oriFileName, srcPath, takeTime, remark, fileSize)
                M_files += 1
                if os.stat(f).st_mode == 33060: # 33060 readonly, 33206 writable
                    os.chmod(f, stat.S_IWRITE)
                    shutil.move(f, t_file) # 파일 이동 후 원본 삭제
                else:
                    shutil.move(f, t_file) # 파일 이동 후 원본 삭제
                    pass
                self.lineEdit_8.setText(str(M_files))
                self.listWidget_2.addItem(oriFileName + ' ' + str(srcPath) +' ' + str(destPath))
                Mfile.append([oriFileName, srcPath, destPath])
            else:
                if os.stat(f).st_mode == 33060: # 33060 readonly, 33206 writable
                    os.chmod(f, stat.S_IWRITE)
                    os.remove(f)
                else:
                    pass
                    os.remove(f)
                R_files += 1
                self.lineEdit_9.setText(str(R_files))
                self.listWidget_4.addItem(str(pathlib.Path(srcPath, oriFileName)))
                Rfile.append([srcPath, destPath, oriFileName])
            cv2.waitKey(10)
        try:
            #self.removeDir()
            #os.rmdir(srcPath)
            pass
        except:
            pass
        self.removeTempFile()
        self.saveExcel(Rfile, 'moveFileExistingFiles.xlsx')
        self.saveExcel(Mfile, 'moveFileMovedFiles.xlsx')
    
    def removeDir(self):
        if self.filesList() == None:
            QMessageBox.about(self, "폴더 재지정", "이동 후 폴더가 존재하지 않습니다")
            return
        else:
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
        self.lineEdit_10.setText('0')
        self.listWidget_2.clear()
        self.listWidget_4.clear()

    def copy_start(self):
        self.copyFile(self.get_pathFileList())
        QMessageBox.about(self, "복사 완료", "파일 복사가 완료 되었습니다")
        return

    def get_pathFileList(self):
        if not self.checkSourceDest():
            self.count_clear()
            fl = pathlib.Path(self.getRootdir(),TEMPFILE)
            if os.path.isfile(fl):
                pathFileList = self.estimateDateFromFileName(self.openExcelFileList(fl))
            else:
                pathFileList = self.estimateDateFromFileName(self.selectListGraphicFiles())
        return pathFileList
    
    def openExcelFileList(self,fl):
        df = pd.read_excel(fl, header=None , skiprows=0)
        return df.values.tolist()


    def move_start(self):
        self.moveFile(self.get_pathFileList())
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
            fname = pathlib.Path(QFileDialog.getExistingDirectory(self, '원본 사진 파일이 있는 디렉토리를 선택하세요', init_dir))
            if len(str(fname)) != 0:
                self.lineEdit.setText(str(fname))
            else:
                self.lineEdit.setText(LE[0])
        else :
            # sname == '정리할 폴더':
            init_dir = self.LE[1]
            fname = pathlib.Path(QFileDialog.getExistingDirectory(self, '사진 파일을 정리해 놓을 디렉토리를 선택하세요', init_dir))
            if len(str(fname)) != 0:
                self.lineEdit_2.setText(str(fname))
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
        self.listWidget.addItem(str(pathlib.Path(path, f)))
        #self.listWidget.addItem(self.addItemText)

class MyCheckBox(QCheckBox):
    def __init__(self, item):
        """
        :param item: QTableWidgetItem instance
        """
        super().__init__()
        self.item = item
        self.mycheckvalue = 0   # 0 --> unchecked, 2 --> checked
        self.stateChanged.connect(self.__checkbox_change)
        self.stateChanged.connect(self.item.my_setdata)  # checked 여부로 정렬을 하기위한 data 저장

    def __checkbox_change(self, checkvalue):
        # print("myclass...check change... ", checkvalue)
        self.mycheckvalue = checkvalue
        print("checkbox row= ", self.get_row())

    def get_row(self):
        return self.item.row()


class MyQTableWidgetItemCheckBox(QTableWidgetItem):
    """
    checkbox widget 과 같은 cell 에  item 으로 들어감.
    checkbox 값 변화에 따라, 사용자정의 data를 기준으로 정렬 기능 구현함.
    """
    def __init__(self):
        super().__init__()
        self.setData(Qt.UserRole, 0)

    def __lt__(self, other):
        # print(type(self.data(Qt.UserRole)))
        return self.data(Qt.UserRole) < other.data(Qt.UserRole)

    def my_setdata(self, value):
        # print("my setdata ", value)
        self.setData(Qt.UserRole, value)
        # print("row ", self.row())

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