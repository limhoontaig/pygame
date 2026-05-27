# ui_main_window.py 수정본
import os
import sqlite3
from datetime import datetime

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QDateEdit, QPushButton, QStackedWidget, QSplitter, 
                             QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog)
from PyQt5.QtCore import QTimer, QDate, Qt

# 🌟 신규 분리한 그래프 매니저 임포트
from ui_graph_manager import GraphManager

import db_manager
import excel_report
from ui_dialogs import ManualMeterInputDialog 

class SCADAWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(10000) 
        self.last_hour = datetime.now().hour

    def initUI(self):
        self.setWindowTitle("래미안개포루체하임아파트 변전실 데이터 통합 관리 시스템 (Developed by 관리과장 임훈택)")
        self.resize(1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # ==================== 상단 제어 센터 ====================
        top_ctrl = QGroupBox("운영 제어 센터")
        top_layout = QHBoxLayout(top_ctrl)
        top_layout.setSpacing(50)
        
        self.qdate = QDateEdit(QDate.currentDate())
        self.qdate.setCalendarPopup(True)
        self.qdate.setMinimumWidth(120) 
        self.qdate.setAlignment(Qt.AlignCenter) 
        self.qdate.setStyleSheet("font-size: 14px; padding: 3px; font-weight: bold;") 
        
        lbl_date_title = QLabel("<b>선택 날짜:</b>")
        lbl_date_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.btn_show_table = QPushButton("종합 데이터 표")
        self.btn_show_table.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; min-height: 35px;")
        self.btn_show_graph = QPushButton("부하 변동 그래프")
        self.btn_show_graph.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; min-height: 35px;")
        self.btn_export_excel = QPushButton("엑셀 운영일지 출력")
        self.btn_export_excel.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; min-height: 35px;")
        self.btn_meter_input = QPushButton("전력량계 검침량 입력") 
        self.btn_meter_input.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; min-height: 35px;")
        
        top_layout.addWidget(lbl_date_title)
        top_layout.addWidget(self.qdate)
        top_layout.addWidget(self.btn_show_table)
        top_layout.addWidget(self.btn_show_graph)
        top_layout.addWidget(self.btn_export_excel)
        top_layout.addWidget(self.btn_meter_input)    
        main_layout.addWidget(top_ctrl)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # ==================== 1. 테이블 탭 구성 ====================
        self.page_table = QWidget()
        table_layout = QVBoxLayout(self.page_table)
        splitter = QSplitter(Qt.Vertical)
        
        self.raw_table = QTableWidget()
        self.raw_table.setColumnCount(len(db_manager.COLUMN_LABELS))
        self.raw_table.setHorizontalHeaderLabels(db_manager.COLUMN_LABELS)
        
        self.avg_table = QTableWidget()
        self.avg_table.setColumnCount(len(db_manager.COLUMN_LABELS))
        self.avg_table.setHorizontalHeaderLabels(db_manager.COLUMN_LABELS)

        self.extreme_table = QTableWidget()
        self.extreme_table.setColumnCount(len(db_manager.COLUMN_LABELS))
        self.extreme_table.setHorizontalHeaderLabels(db_manager.COLUMN_LABELS)

        self.manual_table = QTableWidget()
        manual_headers = ["기록 일자"] + db_manager.METER_FIELDS 
        self.manual_table.setColumnCount(len(manual_headers))
        self.manual_table.setHorizontalHeaderLabels(manual_headers)

        splitter.addWidget(QLabel("● 실시간 계측 데이터 로그"))
        splitter.addWidget(self.raw_table)
        splitter.addWidget(QLabel("● 시간별 평균 전력 추이"))
        splitter.addWidget(self.avg_table)
        splitter.addWidget(QLabel("● 일일 최고(MAX) / 최저(MIN) 값 설비 통계"))
        splitter.addWidget(self.extreme_table)
        splitter.addWidget(QLabel("● 독립 계량장치 일일 지침 수동 로그 (manual_meter_logs)"))
        splitter.addWidget(self.manual_table)

        table_layout.addWidget(splitter)
        self.stack.addWidget(self.page_table)

        # ==================== 2. 그래프 탭 구성 (🌟대폭 다이어트) ====================
        # 복잡했던 레이아웃과 리스트 코드는 전부 ui_graph_manager 내부로 들어갔습니다.
        self.graph_manager = GraphManager(self) 
        self.stack.addWidget(self.graph_manager)

        # ==================== 3. 이벤트 시그널 연결 ====================
        self.btn_show_table.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_show_graph.clicked.connect(self.on_graph_tab_changed) # 변경
        self.btn_export_excel.clicked.connect(self.export_excel_click)
        self.btn_meter_input.clicked.connect(self.click_open_meter_popup)
        self.qdate.dateChanged.connect(self.auto_refresh)

        self.load_data()

    def on_graph_tab_changed(self):
        """그래프 탭으로 전환될 때 즉시 그래프를 그리도록 지시하는 함수"""
        self.stack.setCurrentIndex(1)
        self.graph_manager.update_graph()

    def load_data(self):
        selected_date = self.qdate.date().toString("yyyy-MM-dd")
        db_manager.calculate_daily_extremes(selected_date)
        
        try:
            conn = sqlite3.connect(db_manager.DB_NAME)
            c = conn.cursor()
            
            query_raw = f"SELECT log_date, log_time, {', '.join([f'\"{n}\"' for n in db_manager.DATA_LABELS])} FROM raw_data WHERE log_date = ? ORDER BY log_time DESC"
            c.execute(query_raw, (selected_date,))
            self.display_table(self.raw_table, c.fetchall())
            
            query_avg = f"SELECT log_date, log_time, {', '.join([f'\"{n}\"' for n in db_manager.DATA_LABELS])} FROM hourly_avg WHERE log_date = ? ORDER BY log_time ASC"
            c.execute(query_avg, (selected_date,))
            self.display_table(self.avg_table, c.fetchall())
            
            query_ext = f"SELECT log_date, extreme_type, {', '.join([f'\"{n}\"' for n in db_manager.DATA_LABELS])} FROM daily_extremes WHERE log_date = ? ORDER BY extreme_type DESC"
            c.execute(query_ext, (selected_date,))
            self.display_table(self.extreme_table, c.fetchall(), is_extreme=True)
            
            conn.close()

            if hasattr(db_manager, 'get_manual_meter_log_for_table'):
                manual_row = db_manager.get_manual_meter_log_for_table(selected_date)
                self.display_manual_table([manual_row])

        except Exception as e:
            print(f"UI 로딩 실패: {e}")

    def display_manual_table(self, rows):
        self.manual_table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if c_idx > 0 and val != "-":
                    item.setForeground(Qt.darkGreen)
                self.manual_table.setItem(r_idx, c_idx, item)

    def display_table(self, table, rows, is_extreme=False):
        table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                txt = f"{val:.1f}" if isinstance(val, float) else str(val)
                item = QTableWidgetItem(txt)
                item.setTextAlignment(Qt.AlignCenter)

                if is_extreme and c_idx > 1:
                    if row[1] == 'MAX': item.setForeground(Qt.red)
                    elif row[1] == 'MIN': item.setForeground(Qt.blue)
                table.setItem(r_idx, c_idx, item)

    def export_excel_click(self):
        selected_date = self.qdate.date().toString("yyyy-MM-dd")
        selected_dir = QFileDialog.getExistingDirectory(self, "운영일지 저장 폴더 선택", "")
        if not selected_dir: return  
            
        try:
            excel_report.generate_excel_report(selected_date, target_dir=selected_dir)
            saved_path = os.path.join(selected_dir, f"{selected_date}_전기실_운영일지.xlsx")
            QMessageBox.information(self, "출력 완료", f"성공적으로 엑셀 운영일지가 생성되었습니다.\n\n저장 경로:\n{saved_path}")
        except Exception as e:
            QMessageBox.critical(self, "출력 실패", f"에러 발생:\n{e}")

    def auto_refresh(self):
        curr_hour = datetime.now().hour
        if curr_hour != self.last_hour:
            db_manager.calculate_hourly_avg()
            self.last_hour = curr_hour
        self.load_data()
        self.graph_manager.update_graph() # 분리한 객체의 함수 호출

    def click_open_meter_popup(self):
        current_date_str = self.qdate.date().toString("yyyy-MM-dd")
        dialog = ManualMeterInputDialog(current_date_str, self)
        result = dialog.exec_()
        
        if result == 1: 
            save_date = dialog.date_edit.date().toString("yyyy-MM-dd")
            final_data = {field: edit.text().strip() for field, edit in dialog.inputs.items()}

            reply = QMessageBox.question(
                self, '데이터 저장 확인', f"[{save_date}] 수동 입력 지침을 DB에 반영하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                selected_dir = QFileDialog.getExistingDirectory(self, "운영일지 저장 폴더 선택", "")
                if not selected_dir: return
                try:
                    db_manager.save_manual_meter_data(save_date, final_data)
                    excel_report.generate_excel_report(save_date, target_dir=selected_dir)
                    self.load_data()
                    QMessageBox.information(self, "저장 완료", "성공적으로 처리되었습니다.")
                except Exception as e:
                    QMessageBox.critical(self, "오류 발생", f"에러: {e}")