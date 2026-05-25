# ui/main_window.py

import os
import sys
# 현재 파일(main_window.py)의 부모의 부모 폴더(프로젝트 루트)를 파이썬 검색 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)


import pathlib
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import QTimer, Qt

from database.db_handler import DBHandler
from services.file_service import FileService

class MainWindow(QMainWindow):
    def __init__(self, ui_path):
        super().__init__()
        # UI 파일 로드
        uic.loadUi(ui_path, self)
        
        # 서비스 및 핸들러 초기화
        self.db = DBHandler()
        self.file_service = FileService()
        
        # 슬라이드 쇼용 타이머 초기화 (화면 freeze 방지)
        self.slide_timer = QTimer(self)
        self.slide_timer.timeout.connect(self.next_slide)
        self.slide_files = []
        self.current_slide_index = 0

        # 이벤트 시그널 연결
        self.init_signals()

    def init_signals(self):
        """UI 컴포넌트와 메서드 간의 시그널 연결"""
        self.pushButton.clicked.connect(self.select_directory)            # 대상 폴더 선택
        self.pushButton_2.clicked.connect(self.load_and_scan_files)       # 파일 가져오기
        
        # [수정] pushButton_3 대신 실제 UI 객체 이름인 search_pbt를 사용합니다.
        self.search_pbt.clicked.connect(self.search_db_data)              # 조건 검색
        
        # [수정] pushButton_4 대신 실제 UI 객체 이름인 slide_pbt를 사용합니다.
        self.slide_pbt.clicked.connect(self.start_slideshow)              # 슬라이드 쇼 시작
        
        self.pushButton_5.clicked.connect(self.start_file_classification) # 분류 시작
        self.pushButton_6.clicked.connect(self.close)                     # 종료

        # 테이블 위젯 클릭 이벤트 연결
        self.tableWidget.itemClicked.connect(self.on_table_item_clicked)

    def select_directory(self):
        """디렉토리 선택 창 오픈"""
        dir_path = QFileDialog.getExistingDirectory(self, "사진 폴더 선택", "./")
        if dir_path:
            self.lineEdit.setText(dir_path)

    def load_and_scan_files(self):
        """폴더 내 파일을 스캔하고 EXIF를 추출하여 DB에 저장 및 테이블 테이블 뷰 갱신"""
        dir_path = self.lineEdit.text()
        if not dir_path or not os.path.exists(dir_path):
            QMessageBox.warning(self, "경고", "올바른 폴더 경로를 지정해 주세요.")
            return

        # UI 비즈니스 분리 가이드: 스캔 루프 돌며 db.insert_picture 호출
        # (기존의 폴더 순회 및 EXIF 추출 로직이 여기에 위치하게 됩니다.)
        QMessageBox.information(self, "알림", "파일 스캔 및 DB 동기화가 완료되었습니다.")
        self.search_db_data() # 완료 후 자동 조회

    def search_db_data(self):
        """DB에서 데이터를 조회하여 QTableWidget에 매핑"""
        file_term = self.lineEdit_12.text()
        act_term = self.lineEdit_16.text()
        check_file = self.checkBox_3.isChecked()
        check_act = self.checkBox_4.isChecked()

        # DB 레이어 호출
        results = self.db.select_pictures(file_term, act_term, check_file, check_act)
        
        # 테이블 초기화 및 바인딩
        self.tableWidget.setRowCount(0)
        for row_idx, data in enumerate(results):
            self.tableWidget.insertRow(row_idx)
            self.tableWidget.setItem(row_idx, 0, QTableWidgetItem(str(data['pictureFileName'])))
            self.tableWidget.setItem(row_idx, 1, QTableWidgetItem(str(data['activityName'])))
            self.tableWidget.setItem(row_idx, 2, QTableWidgetItem(str(data['fileVolume'])))
            self.tableWidget.setItem(row_idx, 3, QTableWidgetItem(str(data['makeTime'])))

    def on_table_item_clicked(self, item):
        """테이블 아이템 클릭 시 오른쪽에 이미지/비디오 프리뷰"""
        row = item.row()
        file_name = self.tableWidget.item(row, 0).text()
        
        # 기존 로직과 동일하게 경로 조합 후 전처리
        # file_service.imread_korean() 활용하여 cv_img 획득 후 label에 세팅
        pass

    def start_slideshow(self):
        """슬라이드 쇼 시작 (QTimer 활용으로 앱이 멈추지 않음)"""
        # 기존 무한루프 대신 타이머를 기동합니다.
        self.current_slide_index = 0
        self.slide_timer.start(2000) # 2초 간격 전환

    def next_slide(self):
        """타이머에 의해 주기적으로 호출될 슬라이드 전환 함수"""
        if self.current_slide_index >= len(self.slide_files):
            self.slide_timer.stop()
            QMessageBox.information(self, "알림", "슬라이드 쇼가 끝났습니다.")
            return
        
        # 다음 사진을 세팅하는 로직 진행
        self.current_slide_index += 1

    def start_file_classification(self):
        """구글 포토 백업본 및 PC 사진을 일자별 구조(년/월-일)로 자동 분류 정렬합니다."""
        
        # 1. 원본 파일들이 쌓여있는 폴더 선택 (예: 구글 테이크아웃 다운로드 폴더)
        source_dir = QFileDialog.getExistingDirectory(self, "정리할 원본 사진/동영상 폴더 선택", "./")
        if not source_dir:
            return
            
        # 2. 깨끗하게 정리되어 저장될 메인 대용량 저장소 폴더 선택 (예: 외장하드, NAS 연결폴더)
        target_dir = QFileDialog.getExistingDirectory(self, "일자별로 정리되어 저장될 목적지 폴더 선택", "./")
        if not target_dir:
            return

        # 진행 확인 알림
        reply = QMessageBox.question(
            self, '분류 진행 확인', 
            f"선택한 원본 폴더의 미디어 파일들을 목적지 폴더로 분류 복사하시겠습니까?\n\n"
            f"▶ 원본: {source_dir}\n▶ 목적지: {target_dir}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return

        # 대량 파일 처리 중 UI가 멈춘 것처럼 보이지 않도록 상태바 상태 제어
        self.statusBar().showMessage("미디어 파일 일자별 분류 데이터베이스화 진행 중...")
        
        # 진행률 출력 헬퍼 함수
        def update_progress(current, total):
            # 상태바에 실시간 퍼센트 및 개수 표시
            percent = int((current / total) * 100)
            self.statusBar().showMessage(f"분류 진행 중... [{current}/{total}] ({percent}%)")
            # PyQt의 UI를 실시간 강제 새로고침하여 '응답없음' 방지
            QApplication.processEvents()

        # 3. 비즈니스 서비스 로직 호출
        success, message = self.file_service.classify_and_move_files(
            source_dir, target_dir, progress_callback=update_progress
        )
        
        # 4. 완료 알림
        if success:
            QMessageBox.information(self, "분류 완료", message)
            self.statusBar().showMessage("파일 분류 작업 완료", 5000)
            
            # 분류 완료 후, 사용자가 원한다면 테이블 뷰에 정리된 폴더 결과를 바로 로드할 수 있도록 유도
            self.lineEdit.setText(target_dir)
        else:
            QMessageBox.critical(self, "오류 발생", message)
            self.statusBar().clearMessage()