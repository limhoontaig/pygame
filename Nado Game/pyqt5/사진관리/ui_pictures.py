# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'pictures.ui'
##
## Created by: Qt User Interface Compiler version 6.3.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QProgressBar, QPushButton, QSizePolicy, QTabWidget,
    QTextEdit, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1376, 799)
        self.tabWidget = QTabWidget(Form)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(0, 10, 671, 761))
        self.tabWidget.setTabShape(QTabWidget.Triangular)
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.lineEdit = QLineEdit(self.tab)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setGeometry(QRect(10, 10, 541, 31))
        self.pushButton = QPushButton(self.tab)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setGeometry(QRect(572, 10, 81, 31))
        self.pushButton_2 = QPushButton(self.tab)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setGeometry(QRect(572, 50, 81, 31))
        self.pushButton_3 = QPushButton(self.tab)
        self.pushButton_3.setObjectName(u"pushButton_3")
        self.pushButton_3.setGeometry(QRect(460, 90, 91, 31))
        self.pushButton_4 = QPushButton(self.tab)
        self.pushButton_4.setObjectName(u"pushButton_4")
        self.pushButton_4.setGeometry(QRect(570, 90, 81, 31))
        self.comboBox = QComboBox(self.tab)
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.setObjectName(u"comboBox")
        self.comboBox.setGeometry(QRect(10, 90, 131, 31))
        self.comboBox.setInsertPolicy(QComboBox.InsertAlphabetically)
        self.comboBox_2 = QComboBox(self.tab)
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.setObjectName(u"comboBox_2")
        self.comboBox_2.setGeometry(QRect(200, 90, 121, 31))
        self.lineEdit_2 = QLineEdit(self.tab)
        self.lineEdit_2.setObjectName(u"lineEdit_2")
        self.lineEdit_2.setGeometry(QRect(10, 50, 541, 31))
        self.checkBox = QCheckBox(self.tab)
        self.checkBox.setObjectName(u"checkBox")
        self.checkBox.setGeometry(QRect(20, 135, 131, 21))
        self.checkBox_2 = QCheckBox(self.tab)
        self.checkBox_2.setObjectName(u"checkBox_2")
        self.checkBox_2.setGeometry(QRect(150, 135, 111, 21))
        self.lineEdit_3 = QLineEdit(self.tab)
        self.lineEdit_3.setObjectName(u"lineEdit_3")
        self.lineEdit_3.setGeometry(QRect(270, 130, 381, 31))
        self.listWidget = QListWidget(self.tab)
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setGeometry(QRect(10, 190, 641, 161))
        self.listWidget_2 = QListWidget(self.tab)
        self.listWidget_2.setObjectName(u"listWidget_2")
        self.listWidget_2.setGeometry(QRect(10, 380, 641, 121))
        self.listWidget_3 = QListWidget(self.tab)
        self.listWidget_3.setObjectName(u"listWidget_3")
        self.listWidget_3.setGeometry(QRect(10, 640, 641, 91))
        self.label_10 = QLabel(self.tab)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setGeometry(QRect(20, 170, 631, 16))
        self.label_11 = QLabel(self.tab)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setGeometry(QRect(10, 360, 641, 16))
        self.label_12 = QLabel(self.tab)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setGeometry(QRect(10, 620, 641, 16))
        self.listWidget_4 = QListWidget(self.tab)
        self.listWidget_4.setObjectName(u"listWidget_4")
        self.listWidget_4.setGeometry(QRect(10, 530, 641, 91))
        self.label_13 = QLabel(self.tab)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setGeometry(QRect(10, 510, 641, 16))
        self.pushButton_5 = QPushButton(self.tab)
        self.pushButton_5.setObjectName(u"pushButton_5")
        self.pushButton_5.setGeometry(QRect(350, 90, 93, 28))
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.textEdit = QTextEdit(self.tab_2)
        self.textEdit.setObjectName(u"textEdit")
        self.textEdit.setGeometry(QRect(10, 10, 641, 391))
        self.tabWidget.addTab(self.tab_2, "")
        self.label_8 = QLabel(Form)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setGeometry(QRect(680, 30, 660, 460))
        self.label_8.setFrameShape(QFrame.Box)
        self.label_8.setAlignment(Qt.AlignCenter)
        self.frame = QFrame(Form)
        self.frame.setObjectName(u"frame")
        self.frame.setGeometry(QRect(680, 510, 661, 261))
        self.frame.setFrameShape(QFrame.Box)
        self.frame.setFrameShadow(QFrame.Raised)
        self.frame.setLineWidth(3)
        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 230, 501, 21))
        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(20, 81, 71, 21))
        self.lineEdit_4 = QLineEdit(self.frame)
        self.lineEdit_4.setObjectName(u"lineEdit_4")
        self.lineEdit_4.setGeometry(QRect(110, 80, 111, 21))
        self.lineEdit_4.setAlignment(Qt.AlignCenter)
        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(20, 110, 81, 21))
        self.lineEdit_5 = QLineEdit(self.frame)
        self.lineEdit_5.setObjectName(u"lineEdit_5")
        self.lineEdit_5.setGeometry(QRect(110, 110, 111, 21))
        self.lineEdit_5.setAlignment(Qt.AlignCenter)
        self.lineEdit_6 = QLineEdit(self.frame)
        self.lineEdit_6.setObjectName(u"lineEdit_6")
        self.lineEdit_6.setGeometry(QRect(340, 110, 111, 21))
        self.lineEdit_6.setAlignment(Qt.AlignCenter)
        self.label_4 = QLabel(self.frame)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(250, 110, 81, 21))
        self.lineEdit_8 = QLineEdit(self.frame)
        self.lineEdit_8.setObjectName(u"lineEdit_8")
        self.lineEdit_8.setGeometry(QRect(110, 170, 113, 21))
        self.lineEdit_8.setAlignment(Qt.AlignCenter)
        self.label_5 = QLabel(self.frame)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(20, 140, 81, 16))
        self.label_7 = QLabel(self.frame)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(250, 140, 81, 16))
        self.label_6 = QLabel(self.frame)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(20, 170, 81, 16))
        self.lineEdit_7 = QLineEdit(self.frame)
        self.lineEdit_7.setObjectName(u"lineEdit_7")
        self.lineEdit_7.setGeometry(QRect(110, 140, 113, 21))
        self.lineEdit_7.setAlignment(Qt.AlignCenter)
        self.lineEdit_9 = QLineEdit(self.frame)
        self.lineEdit_9.setObjectName(u"lineEdit_9")
        self.lineEdit_9.setGeometry(QRect(340, 140, 113, 21))
        self.lineEdit_9.setAlignment(Qt.AlignCenter)
        self.label_9 = QLabel(self.frame)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setGeometry(QRect(23, 10, 611, 31))
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label_9.setFont(font)
        self.label_9.setAlignment(Qt.AlignCenter)
        self.progressBar = QProgressBar(self.frame)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setGeometry(QRect(20, 200, 621, 23))
        self.progressBar.setValue(0)

        self.retranslateUi(Form)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.pushButton.setText(QCoreApplication.translate("Form", u"\uc6d0\ubcf8 \ud3f4\ub354", None))
        self.pushButton_2.setText(QCoreApplication.translate("Form", u"\ubaa9\uc801 \ud3f4\ub354", None))
        self.pushButton_3.setText(QCoreApplication.translate("Form", u"\ubcf5    \uc0ac", None))
        self.pushButton_4.setText(QCoreApplication.translate("Form", u"\uc774   \ub3d9", None))
        self.comboBox.setItemText(0, QCoreApplication.translate("Form", u"\ub144/\uc6d4/\uc77c\ubcc4\ub85c \uc815\ub9ac", None))
        self.comboBox.setItemText(1, QCoreApplication.translate("Form", u"\ub144/\uc6d4\ubcc4\ub85c \uc815\ub9ac", None))
        self.comboBox.setItemText(2, QCoreApplication.translate("Form", u"\ub144\ubcc4\ub85c \uc815\ub9ac", None))

        self.comboBox_2.setItemText(0, QCoreApplication.translate("Form", u"2023\ub14402\uc6d408\uc77c", None))
        self.comboBox_2.setItemText(1, QCoreApplication.translate("Form", u"2023-02-08", None))
        self.comboBox_2.setItemText(2, QCoreApplication.translate("Form", u"2023_02_08", None))
        self.comboBox_2.setItemText(3, QCoreApplication.translate("Form", u"20230208", None))
        self.comboBox_2.setItemText(4, QCoreApplication.translate("Form", u"2023.02.08", None))
        self.comboBox_2.setItemText(5, QCoreApplication.translate("Form", u"2023 02 08", None))

        self.checkBox.setText(QCoreApplication.translate("Form", u"\ud558\uc704\ud3f4\ub354 \ubd88\ud3ec\ud568", None))
        self.checkBox_2.setText(QCoreApplication.translate("Form", u"\ud3f4\ub354 \uc124\uba85 \ucd94\uac00", None))
        self.label_10.setText(QCoreApplication.translate("Form", u"\ucd1d \uc791\uc5c5 \ud30c\uc77c \ubaa9\ub85d", None))
        self.label_11.setText(QCoreApplication.translate("Form", u"\uc0ac\uc9c4, \ubcf5\uc0ac \ub610\ub294 \uc774\ub3d9 \ud30c\uc77c \ubaa9\ub85d", None))
        self.label_12.setText(QCoreApplication.translate("Form", u"\uc0ac\uc9c4 \ud30c\uc77c \uc774\uc678\uc758 \ud30c\uc77c \ubaa9\ub85d", None))
        self.label_13.setText(QCoreApplication.translate("Form", u"\uae30\uc874 \uc874\uc7ac \ud30c\uc77c\ub85c \ubcf5\uc0ac\uac00 \uc548\ub418\uac70\ub098 \uc0ad\uc81c(\uc774\ub3d9 \uae30\ub2a5\uc2dc)\ub41c \uc0ac\uc9c4 \ud30c\uc77c \ubaa9\ub85d", None))
        self.pushButton_5.setText(QCoreApplication.translate("Form", u"File List", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("Form", u"\ub0a0\uc9dc\ubcc4 \uc815\ub9ac", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("Form", u"About .....", None))
        self.label_8.setText(QCoreApplication.translate("Form", u"TextLabel", None))
        self.label.setText(QCoreApplication.translate("Form", u"TextLabel", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Total Files", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"Graphic Files", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"Other Files", None))
        self.label_5.setText(QCoreApplication.translate("Form", u"Copyed Files", None))
        self.label_7.setText(QCoreApplication.translate("Form", u"Existed Files", None))
        self.label_6.setText(QCoreApplication.translate("Form", u"Moved Files", None))
        self.lineEdit_9.setText("")
        self.label_9.setText(QCoreApplication.translate("Form", u"\uc18c\uc7a5 \uc0ac\uc9c4\uc758 \uc77c\uc790\ubcc4 \uc0ac\uc9c4 \uc815\ub9ac \ubc0f \ubdf0\uc5b4 \ud504\ub85c\uadf8\ub7a8", None))
    # retranslateUi

