# material_main.py

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import database

from user_approval_dialog import UserApprovalDialog
from material_usage_tab import UsageTab
# 기존에 만든 입고 탭 모듈
from material_inbound_tab import InboundTab 

class MainApp(QMainWindow):
    def __init__(self, user_name):
        super().__init__()
        # 사용자의 변수명을 하나로 통일합니다 (user_name -> current_user)
        self.current_user = user_name
        
        # 1. UI 구조와 메뉴바를 먼저 생성합니다.
        self.init_ui()
        
        # 2. 로그인한 사용자의 권한을 체크하여 메뉴바 노출 여부를 결정합니다.
        self.check_admin_privilege()

    def init_ui(self):
        # 기본 창 설정
        self.setWindowTitle(f"래미안개포루체하임 아파트 자재관리 시스템 - 접속자: {self.current_user}")
        self.resize(1300, 850)

        # --------------------------------------------------
        # [메뉴바 구성] QMainWindow의 menuBar()를 이용합니다.
        # --------------------------------------------------
        menubar = self.menuBar()
        # 나중에 권한 체크 함수에서 제어할 수 있도록 self 키워드를 붙여 변수화합니다.
        self.admin_menu = menubar.addMenu("시스템 관리")
        
        self.action_approval = QAction("신규 가입 신청 승인", self)
        self.action_approval.triggered.connect(self.open_user_approval_dialog)
        self.admin_menu.addAction(self.action_approval)
        # --------------------------------------------------

        # 중앙 탭 위젯 설정
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 1. 자재 입고 탭 추가
        self.tabs.addTab(InboundTab(self.current_user), "자재 입고 입력")

        # 2. 자재 사용 탭 추가
        self.tabs.addTab(UsageTab(self.current_user), "자재 사용 입력")

    def check_admin_privilege(self):
        """현재 로그인한 사용자가 관리자인지 DB에서 확인하여 권한을 제어합니다."""
        is_admin = False
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            # users 테이블에서 현재 로그인한 유저의 관리자 여부(is_admin)를 조회합니다.
            cursor.execute("SELECT is_admin FROM users WHERE username = ?", (self.current_user,))
            result = cursor.fetchone()
            conn.close()
            
            # 관리자(is_admin 값이 1)이거나 아이디 자체가 'admin' 또는 '관리자'인 경우
            if result and result[0] == 1:
                is_admin = True
            elif self.current_user in ['admin', '관리자']:
                is_admin = True
                
        except Exception as e:
            print(f"관리자 권한 확인 중 오류 발생: {e}")
            
        # 권한 유무에 따른 메뉴바 표시 제어
        if is_admin:
            self.admin_menu.setTitle("시스템 관리 (관리자 권한)")
            self.admin_menu.menuAction().setVisible(True)
            self.action_approval.setVisible(True)
            print(f"[{self.current_user}] 관리자 권한 메뉴 활성화 완료")
        else:
            # 일반 사용자에겐 메뉴 자체를 완전히 숨깁니다.
            self.admin_menu.menuAction().setVisible(False)
            print(f"[{self.current_user}] 일반 사용자 - 관리자 메뉴 숨김 처리")

    def open_user_approval_dialog(self):
        """[신규 가입 신청 승인] 메뉴를 누르면 실행되는 함수"""
        dialog = UserApprovalDialog()
        # 모달 창으로 띄워 관리자 작업이 끝나기 전까지 메인 화면을 제어하지 못하게 잠급니다.
        dialog.exec_()