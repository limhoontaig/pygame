from PyQt5.QtWidgets import *


class TableWidget(QTableWidget):
    def __init__(self, parent=None):
        QTableWidget.__init__(self, parent)
        self.setColumnCount(3)
        self.setRowCount(3)

    def contextMenuEvent(self, event):
        """
        ContextMenuPolicy --> DefaultContextMenu
        """
        print(event.pos())
        print(self.mapToGlobal(event.pos()))
        
        menu = QMenu(self)
        copy_action = menu.addAction("복사하기")
        quit_action = menu.addAction("Quit")

        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == quit_action:
            qApp.quit()
        elif action == copy_action:
            print("copy...")


if __name__ == "__main__":
    import sys

    app = QApplication([])
    tableWidget = TableWidget()
    tableWidget.show()
    sys.exit(app.exec_())