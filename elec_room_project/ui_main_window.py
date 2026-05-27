# ui_main_window.py
import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QDateEdit, QPushButton, QStackedWidget, QSplitter, 
                             QTableWidget, QTableWidgetItem, QComboBox, QListWidget, QAbstractItemView, QMessageBox, QFileDialog)
from PyQt5.QtCore import QTimer, QDate, Qt

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# 커스텀 기능 및 팝업창 모듈 로드
import db_manager
import excel_report
from ui_dialogs import ManualMeterInputDialog # 💡 분리한 팝업창 임포트

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

class SCADAWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(10000) 
        self.last_hour = datetime.now().hour

    def initUI(self):
        self.setWindowTitle("래미안개포루체하임아파트 변전실 데이터 통합 관리 시스템 (모듈화 프로젝트: Developed by 관리과장 임훈택 on 2026-05-24)")
        self.resize(1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        top_ctrl = QGroupBox("운영 제어 센터")
        top_layout = QHBoxLayout(top_ctrl)
        top_layout.setSpacing(50)
        
        self.qdate = QDateEdit(QDate.currentDate())
        self.qdate.setCalendarPopup(True)
        
        lbl_date_title = QLabel("<b>선택 날짜:</b>")
        lbl_date_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_date_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        top_layout.addWidget(lbl_date_title)
        top_layout.addWidget(self.qdate)

        self.qdate.setMinimumWidth(120) 
        self.qdate.setAlignment(Qt.AlignCenter) 
        self.qdate.setStyleSheet("font-size: 14px; padding: 3px; font-weight: bold;") 
        
        self.btn_show_table = QPushButton("종합 데이터 표")
        self.btn_show_table.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; min-height: 35px;")
        self.btn_show_graph = QPushButton("부하 변동 그래프")
        self.btn_show_graph.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; min-height: 35px;")
        self.btn_export_excel = QPushButton("엑셀 운영일지 출력")
        self.btn_export_excel.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; min-height: 35px;")
        
        self.btn_meter_input = QPushButton("전력량계 검침량 입력") 
        self.btn_meter_input.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; min-height: 35px;")
        self.btn_meter_input.clicked.connect(self.click_open_meter_popup)
        
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

        # ==================== 2. 그래프 탭 구성 ====================
        self.page_graph = QWidget()
        graph_layout = QVBoxLayout(self.page_graph)
        
        graph_ctrl = QHBoxLayout()
        
        # [왼쪽 축] 다중 선택 리스트 위젯
        self.data_selector = QListWidget()
        self.data_selector.setSelectionMode(QAbstractItemView.MultiSelection) 
        self.data_selector.addItems(db_manager.DATA_LABELS)
        self.data_selector.setMaximumHeight(80) 
        
        # [오른쪽 보조축] 다중 선택 리스트 위젯
        self.right_axis_selector = QListWidget()
        self.right_axis_selector.setSelectionMode(QAbstractItemView.MultiSelection)
        self.right_axis_selector.setMaximumHeight(80) 

        self.period_selector = QComboBox()
        self.period_selector.addItems(["일간 (실시간 데이터)", "주간 (시간별 평균)", "월간 (시간별 평균)"])
        
        graph_ctrl.addWidget(QLabel("기본(왼쪽) 축 필드 선택:"))
        graph_ctrl.addWidget(self.data_selector)
        graph_ctrl.addWidget(QLabel("➡️ 오른쪽(보조) 축으로 보낼 필드:")) 
        graph_ctrl.addWidget(self.right_axis_selector)     
        graph_ctrl.addWidget(QLabel("조회 기간:"))
        graph_ctrl.addWidget(self.period_selector)
        graph_layout.addLayout(graph_ctrl)

        self.canvas = FigureCanvas(Figure(figsize=(8, 5)))
        self.ax = self.canvas.figure.add_subplot(111)
        graph_layout.addWidget(self.canvas)
        self.stack.addWidget(self.page_graph)

        # ==================== 3. 초기 상태 지정 및 이벤트 연결 ====================
        # ⚠️ 중요: UI 컴포넌트가 온전히 로드되기 전까지 강제 팅김을 막기 위해 시그널을 잠시 차단합니다.
        self.data_selector.blockSignals(True)
        self.right_axis_selector.blockSignals(True)

        if self.data_selector.count() > 0:
            self.data_selector.item(0).setSelected(True)
        
        # 기본 데이터를 마운트 시켜 놓습니다.
        self.load_data()
        
        # 모든 구조 작성이 완료된 시점에 비로소 안전하게 이벤트를 연결합니다.
        self.btn_show_table.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_show_graph.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.btn_export_excel.clicked.connect(self.export_excel_click)
        
        self.qdate.dateChanged.connect(self.auto_refresh)
        self.period_selector.currentIndexChanged.connect(self.update_graph)
        
        # 이벤트 등록
        self.data_selector.itemSelectionChanged.connect(self.sync_right_axis_list)
        self.right_axis_selector.itemSelectionChanged.connect(self.update_graph)

        # 잠금을 해제하여 상호 운용을 개시합니다.
        self.data_selector.blockSignals(False)
        self.right_axis_selector.blockSignals(False)
        
        # 첫 화면 렌더링
        self.update_graph()

    def sync_right_axis_list(self):
        """왼쪽 리스트 변경 시 오른쪽 리스트를 실시간 동기화하되, 재귀 루프를 차단합니다."""
        # 무한 루프로 인한 프로그램 다운 방지 핵심 구간
        self.data_selector.blockSignals(True)
        self.right_axis_selector.blockSignals(True)
        
        try:
            prev_selected = [item.text() for item in self.right_axis_selector.selectedItems()]
            left_selected = [item.text() for item in self.data_selector.selectedItems()]
            
            self.right_axis_selector.clear()
            if left_selected:
                self.right_axis_selector.addItems(left_selected)
                for i in range(self.right_axis_selector.count()):
                    item = self.right_axis_selector.item(i)
                    if item.text() in prev_selected:
                        item.setSelected(True)
        finally:
            self.data_selector.blockSignals(False)
            self.right_axis_selector.blockSignals(False)
        
        self.update_graph()

    def update_graph(self):
        """양방향 멀티 초이스 기능이 안전하게 처리되는 그래프 업데이트 스크립트"""
        if self.stack.currentIndex() != 1: return
        
        selected_items = self.data_selector.selectedItems()
        if not selected_items:
            self.canvas.figure.clf()
            self.ax = self.canvas.figure.add_subplot(111)
            self.ax.text(0.5, 0.5, "비교할 필드를 선택해주세요.", ha='center')
            self.canvas.draw()
            return
            
        target_cols = [item.text() for item in selected_items]
        period = self.period_selector.currentText()
        selected_date = self.qdate.date().toPyDate()

        # 양방향 분리 매핑 로직
        right_cols = [item.text() for item in self.right_axis_selector.selectedItems()]
        right_cols = [col for col in right_cols if col in target_cols] # 유효성 검증 예외처리
        left_cols = [col for col in target_cols if col not in right_cols]

        cols_str = ', '.join([f'"{col}"' for col in target_cols])
        
        try:
            conn = sqlite3.connect(db_manager.DB_NAME)
            if "일간" in period:
                query = f'SELECT log_time, {cols_str} FROM raw_data WHERE log_date = ? ORDER BY log_time ASC'
                params = (selected_date.strftime('%Y-%m-%d'),)
            else:
                days = 7 if "주간" in period else 30
                start_date = selected_date - timedelta(days=days)
                query = f'SELECT log_date || \' \' || SUBSTR(log_time,1,5) as dt, {cols_str} FROM hourly_avg WHERE log_date BETWEEN ? AND ? ORDER BY log_date, log_time'
                params = (start_date.strftime('%Y-%m-%d'), selected_date.strftime('%Y-%m-%d'))

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
        except Exception as e:
            print(f"그래프 DB 조회 에러 발생: {e}")
            return

        self.canvas.figure.clf()
        self.ax = self.canvas.figure.add_subplot(111)
        
        if not df.empty:
            x_col = 'log_time' if "일간" in period else 'dt'
            all_lines = []
            
            # [1] 기본 축 - 왼쪽 렌더링
            for col in left_cols:
                if col in df.columns:
                    line = self.ax.plot(df[x_col], df[col], marker='o', markersize=2, label=col)
                    all_lines += line
            
            if left_cols:
                self.ax.set_ylabel(', '.join(left_cols[:2]) + ('...' if len(left_cols) > 2 else ''), color='#1f77b4', fontweight='bold')
                self.ax.tick_params(axis='y', labelcolor='#1f77b4')
            else:
                self.ax.yaxis.set_visible(False)

            # [2] 보조 축 - 오른쪽 다중 렌더링
            if right_cols:
                ax2 = self.ax.twinx()
                for col in right_cols:
                    if col in df.columns:
                        line = ax2.plot(df[x_col], df[col], marker='^', markersize=3, linestyle='--', label=f"{col} (우)")
                        all_lines += line
                
                ax2.set_ylabel(', '.join(right_cols[:2]) + ('...' if len(right_cols) > 2 else ''), color='#ff7f0e', fontweight='bold')
                ax2.tick_params(axis='y', labelcolor='#ff7f0e')
                ax2.grid(False) 

            # 통합 범례(Legend) 연출
            if all_lines:
                labels = [l.get_label() for l in all_lines]
                self.ax.legend(all_lines, labels, loc='upper right')
                
            import matplotlib.ticker as ticker
            self.ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
            self.ax.set_title(f"선택 필드 {period} 분석 (양방향 멀티 축 제어)", fontsize=13, fontweight='bold')
            self.ax.grid(True, linestyle='--')
            self.canvas.figure.autofmt_xdate() 
        else:
            self.ax.text(0.5, 0.5, "데이터가 존재하지 않습니다.", ha='center')
        
        self.canvas.draw()

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
        if not selected_dir:
            return  
            
        try:
            excel_report.generate_excel_report(selected_date, target_dir=selected_dir)
            saved_path = os.path.join(selected_dir, f"{selected_date}_전기실_운영일지.xlsx")
            QMessageBox.information(
                self, "출력 완료", 
                f"성공적으로 엑셀 운영일지가 생성되었습니다.\n\n저장 경로:\n{saved_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "출력 실패", f"에러 발생:\n{e}")

    def auto_refresh(self):
        curr_hour = datetime.now().hour
        if curr_hour != self.last_hour:
            db_manager.calculate_hourly_avg()
            self.last_hour = curr_hour
        self.load_data()
        self.update_graph()

    def click_open_meter_popup(self):
        current_date_str = self.qdate.date().toString("yyyy-MM-dd")
        dialog = ManualMeterInputDialog(current_date_str, self)
        result = dialog.exec_()
        
        if result == 1: 
            save_date = dialog.date_edit.date().toString("yyyy-MM-dd")
            final_data = {}
            try:
                for field, edit in dialog.inputs.items():
                    final_data[field] = edit.text().strip()
            except Exception as e:
                return

            reply = QMessageBox.question(
                self, '데이터 저장 확인',
                f"[{save_date}] 수동 입력 지침을 DB에 반영하시겠습니까?\n(Yes 선택 시 운영일지 출력이 함께 진행됩니다.)",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            
            selected_dir = None
            if reply == QMessageBox.Yes:
                selected_dir = QFileDialog.getExistingDirectory(self, "운영일지 저장 폴더 선택 (DB 저장 후 자동 출력)", "")
                if not selected_dir:
                    QMessageBox.warning(self, "작업 취소", "폴더가 선택되지 않아 DB 저장 및 엑셀 출력 작업이 취소되었습니다.")
                    return

            try:
                db_manager.save_manual_meter_data(save_date, final_data)
                success_msg = f"[{save_date}] 일자의 데이터가 DB에 안전하게 반영되었습니다."
                
                if reply == QMessageBox.Yes and selected_dir:
                    excel_report.generate_excel_report(save_date, target_dir=selected_dir)
                    saved_path = os.path.join(selected_dir, f"{save_date}_전기실_운영일지.xlsx")
                    success_msg += f"\n\n이어서 엑셀 운영일지 출력이 완료되었습니다.\n저장 경로:\n{saved_path}"
                
                QMessageBox.information(self, "저장 완료", success_msg)
                
                if hasattr(self, 'refresh_data'):
                    self.refresh_data()
                elif hasattr(self, 'load_data'):
                    self.load_data()
                
            except Exception as e:
                QMessageBox.critical(self, "오류 발생", f"작업 중 에러가 발생했습니다:\n{str(e)}")
        else:
            print("=== [DEBUG] 사용자가 입력을 취소함 ===")