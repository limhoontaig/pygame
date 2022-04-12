# coding: utf-8

import sys
import os
from PyQt5 import QtWidgets
from PyQt5 import uic

print(sys.path)
path_cwd = os.getcwd()
sys.path.append(path_cwd)
class Form(QtWidgets.QDialog):
  def __init__(self, parent=None):
    QtWidgets.QDialog.__init__(self, parent)
    self.ui = uic.loadUi("E:\pyqt5\Form.ui")
    self.ui.show()

if __name__ == '__main__':
  app = QtWidgets.QApplication(sys.argv)
  w = Form()
  sys.exit(app.exec())
  