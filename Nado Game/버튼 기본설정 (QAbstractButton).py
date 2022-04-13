import os
import sys

from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

#============================  class 설정 부분  =======================================
def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form = resource_path('main.ui')
form_class = uic.loadUiType(form)[0]

class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super( ).__init__( )
        self.setupUi(self)
#==========================  Signal & Setting 부분  ===================================
        # btn_autoReaeat에 반복 적용, Dealy 3000msec, Interval 1000msec
        self.btn_autoRepeat.clicked.connect(self.fnc_autoRepeat)
        self.btn_autoRepeat.setAutoRepeat(True)
        self.btn_autoRepeat.setAutoRepeatDelay(3000)
        self.btn_autoRepeat.setAutoRepeatInterval(1000)

        # btn_chk_1,2에 Checkable 설정, Checked 설정, AotoExclusive 설정
        self.btn_chk_1.clicked.connect(self.fnc_chk_1)
        self.btn_chk_2.clicked.connect(self.fnc_chk_2)
        self.btn_chk_1.setCheckable(True)
        self.btn_chk_2.setCheckable(True)
        self.btn_chk_1.setAutoExclusive(True)
        self.btn_chk_2.setAutoExclusive(True)

        self.btn_chk_3.setCheckable(True)

        # btn_down에 Down 설정.
        self.btn_down.released.connect(self.fnc_down)
        self.btn_down.setDown(True)

        # btn_icon에 setIcon 설정, setText 설정, setShortcut 설정
        self.btn_icon.clicked.connect(self.fnc_icon)
        self.btn_icon.setIcon(QIcon('pandas.png'))
        self.btn_icon.setIconSize(QSize(60,80))
        self.btn_icon.setText('Ctrl+G') # 반드시 shortcut 전에 해야함
        self.btn_icon.setShortcut("Ctrl+G")

        # btn_group 들을 그룹화 후, group 확인
        self.BtnGroup = QButtonGroup()
        self.BtnGroup.addButton(self.btn_group_1, 1)
        self.BtnGroup.addButton(self.btn_group_2, 2)
        self.BtnGroup.addButton(self.btn_group_3, 3)
        self.BtnGroup.addButton(self.btn_group_4, 4)
        self.BtnGroup.buttonClicked.connect(self.fnc_group)

        # nextCheckState 설정
        self.btn_next.clicked.connect(self.fnc_next)
        self.chk_1.setTristate(True)

        # click / toggle / animate 설정
        self.btn_click.clicked.connect(self.fnc_click)
        self.btn_animate.clicked.connect(self.fnc_animate)
        self.btn_toggle.clicked.connect(self.fnc_toggle)

        # signals
        self.btn_clicked.clicked.connect(self.fnc_signals)
        self.btn_pressed.pressed.connect(self.fnc_signals)
        self.btn_released.released.connect(self.fnc_signals)
        self.chk_toggled.toggled.connect(self.fnc_signals)

#===============================  Slot 부분   =========================================
    def fnc_autoRepeat(self):
        print('repeat')
        print(self.btn_autoRepeat.autoRepeat())
        print(self.btn_autoRepeat.autoRepeatDelay())
        print(self.btn_autoRepeat.autoRepeatInterval())

    def fnc_chk_1(self):
        print('chk1 checked')
        print(self.btn_chk_1.isCheckable())
        print(self.btn_chk_1.isChecked())
        print(self.btn_chk_1.autoExclusive())
        self.btn_chk_3.setChecked(True)

    def fnc_chk_2(self):
        print('chk2 checked')
        print(self.btn_chk_2.isCheckable())
        print(self.btn_chk_2.isChecked())
        print(self.btn_chk_2.autoExclusive())
        self.btn_chk_3.setChecked(False)

    def fnc_down(self):
        print('down')
        print(self.btn_down.isDown())

    def fnc_icon(self):
        print(self.btn_icon.icon())
        print(self.btn_icon.iconSize())
        print(self.btn_icon.text())
        print(self.btn_icon.shortcut())

    def fnc_group(self):
        print('group')
        print(self.btn_group_1.group())

    def fnc_next(self):
        print('nextCheckState')
        self.chk_1.nextCheckState()

    def fnc_click(self):
        self.btn_target.click()
        print('click')

    def fnc_animate(self):
        self.btn_target.animateClick(msecs=1000)
        print('animateClicked')

    def fnc_toggle(self):
        self.chk_2.toggle()
        print('toggle')

    def fnc_signals(self):
        print('signal')

#==============================  app 실행 부분  =======================================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = WindowClass( )
    myWindow.show( )
    app.exec_( )