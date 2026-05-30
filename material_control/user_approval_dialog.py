# user_approve_dialog.py

from PyQt5.QtWidgets import *
import database

class UserApprovalDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("신규 가입 신청 승인 관리")
        self.resize(400, 300)
        self.init_ui()
        self.load_pending_users()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.list_widget = QListWidget()
        layout.addWidget(QLabel("승인 대기 중인 사용자 목록:"))
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        btn_approve = QPushButton("선택 승인")
        btn_approve.setStyleSheet("background-color: green; color: white;")
        btn_approve.clicked.connect(self.approve_user)
        
        btn_reject = QPushButton("선택 거절")
        btn_reject.setStyleSheet("background-color: red; color: white;")
        btn_reject.clicked.connect(self.reject_user)
        
        btn_layout.addWidget(btn_approve)
        btn_layout.addWidget(btn_reject)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
    def load_pending_users(self):
        self.list_widget.clear()
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE status = 'PENDING'")
        for row in cursor.fetchall():
            self.list_widget.addItem(row[0])
        conn.close()
        
    def approve_user(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item: return
        username = selected_item.text()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status = 'APPROVED' WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "완료", f"'{username}' 계정이 승인되었습니다.")
        self.load_pending_users()

    def reject_user(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item: return
        username = selected_item.text()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status = 'REJECTED' WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "완료", f"'{username}' 계정 신청을 거절했습니다.")
        self.load_pending_users()