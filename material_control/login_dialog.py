# login_dialog.py

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import database

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.logged_in_user = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('자재관리 시스템 인증')
        self.resize(360, 240)
        
        main_layout = QVBoxLayout()
        
        # 탭 위젯 생성 (로그인 / 회원가입 전환용)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_login_tab(), "로그인")
        self.tabs.addTab(self.create_register_tab(), "신규 가입 신청")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        
    def create_login_tab(self):
        """로그인 입력 폼 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        self.txt_login_user = QLineEdit()
        self.txt_login_user.setPlaceholderText("사용자 이름 입력")
        
        self.txt_login_pw = QLineEdit()
        self.txt_login_pw.setEchoMode(QLineEdit.Password)
        self.txt_login_pw.setPlaceholderText("비밀번호 입력")
        
        form_layout.addRow("사용자명:", self.txt_login_user)
        form_layout.addRow("비밀번호:", self.txt_login_pw)
        layout.addLayout(form_layout)
        
        btn_login = QPushButton('로그인')
        btn_login.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 30px;")
        btn_login.clicked.connect(self.try_login)
        layout.addWidget(btn_login)
        
        widget.setLayout(layout)
        return widget
        
    def create_register_tab(self):
        """신규 가입 신청 폼 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        self.txt_reg_user = QLineEdit()
        self.txt_reg_pw = QLineEdit()
        self.txt_reg_pw.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("신청 사용자명:", self.txt_reg_user)
        form_layout.addRow("설정 비밀번호:", self.txt_reg_pw)
        layout.addLayout(form_layout)
        
        btn_register = QPushButton('가입 신청하기')
        btn_register.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; height: 30px;")
        btn_register.clicked.connect(self.try_register)
        layout.addWidget(btn_register)
        
        lbl_info = QLabel("※ 신청 후 관리자의 승인이 있어야 로그인이 가능합니다.")
        lbl_info.setStyleSheet("color: gray;")
        lbl_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_info)
        
        widget.setLayout(layout)
        return widget

    def try_login(self):
        """로그인 처리 및 검증"""
        username = self.txt_login_user.text().strip()
        password = self.txt_login_pw.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "경고", "사용자명과 비밀번호를 모두 입력해주세요.")
            return
            
        hashed_pw = database.hash_password(password)
        
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status FROM users 
                WHERE username = ? AND password = ?
            """, (username, hashed_pw))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                status = result[0]
                if status == 'APPROVED':
                    self.logged_in_user = username
                    self.accept() # 로그인 성공 처리 및 창 닫기
                elif status == 'PENDING':
                    QMessageBox.information(self, "안내", "현재 승인 대기 중인 계정입니다.\n관리자 승인 후 접속 가능합니다.")
                elif status == 'REJECTED':
                    QMessageBox.warning(self, "거절", "가입 신청이 거절된 계정입니다. 관리자에게 문의하세요.")
            else:
                QMessageBox.critical(self, "오류", "사용자명 또는 비밀번호가 일치하지 않습니다.")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"로그인 중 오류가 발생했습니다: {e}")

    def try_register(self):
        """신규 가입 신청 등록 처리"""
        username = self.txt_reg_user.text().strip()
        password = self.txt_reg_pw.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "경고", "신청할 사용자명과 비밀번호를 입력해주세요.")
            return
            
        hashed_pw = database.hash_password(password)
        
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            
            # 중복 ID 체크
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(self, "중복 신청", "이미 존재하거나 신청된 사용자 이름입니다.")
                conn.close()
                return
                
            # 신규 신청 데이터 삽입 (기본 승인 상태: PENDING)
            cursor.execute("""
                INSERT INTO users (username, password, status, is_admin) 
                VALUES (?, ?, 'PENDING', 0)
            """, (username, hashed_pw))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "신청 완료", f"'{username}'님 가입 신청이 완료되었습니다.\n관리자 승인 후 로그인해 주세요.")
            # 가입 완료 후 로그인 탭으로 이동 및 입력창 초기화
            self.txt_reg_user.clear()
            self.txt_reg_pw.clear()
            self.tabs.setCurrentIndex(0)
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"신청 중 오류가 발생했습니다: {e}")
            
    def get_logged_in_user(self):
        return self.logged_in_user