import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt

class ListWidget(QListWidgetItem):
    def __lt__(self, other):
        try:
            print(self.text()), float(other.text())
            return float(self.text()) < float(other.text())
        except:
            return QListWidgetItem.__lt__(self, other)


class AppDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(800, 1000)
        self.setStyleSheet('font-size: 50px;')

        layout = QVBoxLayout()

        buttonAsc = QPushButton('Sort Ascending')
        buttonAsc.clicked.connect(self.sortItemsAscending)
        layout.addWidget(buttonAsc)

        buttonDesc = QPushButton('Sort Descending')
        buttonDesc.clicked.connect(self.sortItemsDescending)
        layout.addWidget(buttonDesc)


        self.listWidget = QListWidget()
        layout.addWidget(self.listWidget)

        vals = [10, 140, 45, 4, 455, 15, 1]

        for v in vals:          
            # self.listWidget.addItem(str(v))
            self.listWidget.addItem(ListWidget(str(v)))

        self.setLayout(layout)

    def sortItemsAscending(self):
        self.listWidget.sortItems()

    def sortItemsDescending(self):
        self.listWidget.sortItems(Qt.DescendingOrder)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    demo = AppDemo()
    demo.show()

    try:
        sys.exit(app.exec_())
    except SystemExit:
        print('Closing Window...')

