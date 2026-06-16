# material_main.py

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import database

from user_approval_dialog import UserApprovalDialog
from material_usage_tab import UsageTab
# 기존에 만든 입고 탭 모듈
from material_inbound_tab import InboundTab 
from material_stock_tab import StockTab
from material_fifo_tab import FifoStatusTab

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

        # --------------------------------------------------
        # [상태 표시줄 추가] 현재 어떤 작업을 하고 있는지 하단에 명시
        # --------------------------------------------------
        self.statusbar = self.statusBar()
        self.statusbar.showMessage("시스템이 준비되었습니다. 작업을 선택하세요.")
        # --------------------------------------------------

        # 중앙 탭 위젯 설정
        self.tabs = QTabWidget()
        
        # [디자인 업그레이드] 스타일시트(QSS) 적용으로 현재 운영 중인 탭을 확실하게 강조
        self.apply_tab_style()
        
        self.setCentralWidget(self.tabs)

        # 1. 탭 객체들을 '먼저' 전부 생성합니다.
        self.inbound_tab = InboundTab(self.current_user)
        self.usage_tab = UsageTab(self.current_user)
        self.stock_tab = StockTab(self.current_user)  # 이제 안전하게 생성됨
        self.fifo_tab = FifoStatusTab(self.current_user)  # FIFO 재고 탭 추가

        # 2. QTabWidget에 탭들을 추가합니다.
        self.tabs.addTab(self.inbound_tab, "자재 입고 입력")
        self.tabs.addTab(self.usage_tab, "자재 사용 입력")
        self.tabs.addTab(self.stock_tab, "자재 현재고 조회")
        self.tabs.addTab(self.fifo_tab, "FIFO 재고 조회")

        # 5. [옵션] 사용자가 다른 탭에서 입고/출고를 입력한 후 재고 탭으로 이동했을 때 
        # 자동으로 최신 재고가 새로고침되도록 이벤트 시그널을 연결해주면 아주 편리합니다.
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # 프로그램 시작 시 첫 번째 탭 안내 문구 출력
        self.update_status_message(0)

    def apply_tab_style(self):
        """탭 위젯의 시각적 식별성을 높이기 위한 스타일시트 적용"""
        tab_style = """
            QTabWidget::pane { 
                border: 1px solid #C4C4C4; 
                background: white;
            }
            QTabBar::tab {
                background: #E1E1E1;
                color: #333333;
                border: 1px solid #C4C4C4;
                border-bottom-color: none; /* 본문과 연결되도록 아래 테두리 제거 */
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: normal;
                min-width: 120px;
            }
            QTabBar::tab:hover {
                background: #D2D2D2;
            }
            /* 현재 활성화된(운영 중인) 탭 스타일 - 진한 파란색 계열 배경과 흰색 글씨로 강조 */
            QTabBar::tab:selected {
                background: #2B579A; 
                color: white;
                font-weight: bold;
                border-color: #2B579A;
            }
        """
        self.tabs.setStyleSheet(tab_style)

    def update_status_message(self, index):
        """현재 선택된 탭에 맞춰 하단 상태 표시줄 메시지를 변경합니다."""
        tab_text = self.tabs.tabText(index)
        self.statusbar.showMessage(f"현재 작업 공간: [{tab_text}] — 데이터를 입력하거나 조회하는 중입니다.")

    def on_tab_changed(self, index):
        """탭이 전환될 때 자동으로 데이터를 리로드하고 상태창을 변경하는 트리거 기능"""
        # 하단 상태창 문구 업데이트
        self.update_status_message(index)

        # 만약 선택된 탭이 '자재 현재고 조회' 탭(index: 2)이라면 자동으로 리프레시 실행
        if index == 2:
            self.stock_tab.load_stock_data()

        if index == 3: # 4번째 탭 인덱스
            self.fifo_tab.load_item_combobox()
            self.fifo_tab.calculate_and_display_fifo()    

    def check_admin_privilege(self):
        """현재 로그인한 사용자가 관리자인지 DB에서 확인하여 권한을 제어합니다."""
        is_admin = False
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            # users 테이블에서 현재 로그인한 유저의 관리자 여부(is_admin)를 조회합니다.
            cursor.execute("SELECT is_admin FROM users WHERE username = %s", (self.current_user,))
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