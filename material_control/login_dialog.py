from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import database

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_users()
        
    def init_ui(self):
        self.setWindowTitle('자재관리 시스템 로그인')
        self.resize(320, 160)
        
        # 레이아웃 구성
        layout = QVBoxLayout()
        
        lbl_title = QLabel('접속자를 선택해 주세요')
        lbl_title.setAlignment(Qt.AlignCenter)
        font = lbl_title.font()
        font.setPointSize(11)
        font.setBold(True)
        lbl_title.setFont(font)
        layout.addWidget(lbl_title)
        
        # 사용자 선택 콤보박스
        self.combo_user = QComboBox()
        layout.addWidget(self.combo_user)
        
        # 로그인 버튼
        self.btn_login = QPushButton('로그인')
        self.btn_login.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 30px;")
        self.btn_login.clicked.connect(self.accept) # 성공 시 Accepted 리턴하고 창 닫힘
        layout.addWidget(self.btn_login)
        
        self.setLayout(layout)
        
    def load_users(self):
        """DB에서 사용자 명단을 가져와 콤보박스에 추가합니다."""
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users")
            users = cursor.fetchall()
            for user in users:
                self.combo_user.addItem(user[0])
            conn.close()
        except Exception as e:
            # DB가 없거나 연결 오류 시 임시 데이터 추가
            self.combo_user.addItems(['관리자', '작업자A'])
            
    def get_logged_in_user(self):
        """선택된 사용자 이름을 반환합니다."""
        return self.combo_user.currentText()