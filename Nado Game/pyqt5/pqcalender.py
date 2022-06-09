import sys

from PyQt5 import QtCore, QtWidgets


class DateEdit(QtWidgets.QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent, calendarPopup=True)
        self._today_button = QtWidgets.QPushButton(self.tr("Today"))
        self._today_button.clicked.connect(self._update_today)
        self.calendarWidget().layout().addWidget(self._today_button)

    #@QtCore.pyqtSlot()
    def _update_today(self):
        self._today_button.clearFocus()
        today = QtCore.QDate.currentDate()
        self.calendarWidget().setSelectedDate(today)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = DateEdit()
    w.show()
    sys.exit(app.exec_())