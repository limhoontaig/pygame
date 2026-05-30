# material_main.py

import sys
from PyQt5.QtWidgets import *
from material_usage_tab import UsageTab
# 여기서 기존에 만든 입고 탭 모듈도 가져옵니다.
from material_inbound_tab import InboundTab 

class MainApp(QMainWindow):
    def __init__(self, user_name):
        super().__init__()
        self.user_name = user_name
        self.setWindowTitle(f"강남데시앙파크 자재관리 시스템 - 접속자: {user_name}")
        self.resize(1300, 850)

        # 중앙 탭 위젯 설정
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 1. 자재 입고 탭 추가 (기존 코드를 클래스로 변환하여 연결)
        self.tabs.addTab(InboundTab(self.user_name), "자재 입고 입력")

        # 2. 자재 사용 탭 추가
        self.tabs.addTab(UsageTab(self.user_name), "자재 사용 입력")

        # 3. (예정) 재고 조회 탭 등...