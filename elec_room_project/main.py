import sys
import threading
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, QLabel, QHBoxLayout, 
                             QDateEdit, QComboBox, QGroupBox, QSplitter, QStackedWidget, QMessageBox)
from PyQt5.QtCore import QTimer, QDate, Qt
# main.py 상단에 추가할 내용 (QFormLayout 추가)
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QGridLayout, QDateEdit, QDialogButtonBox, QGroupBox, QFormLayout

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# 💡 직접 만든 커스텀 기능 모듈들을 가져옵니다!
import db_manager
import plc_worker
import excel_report

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

class ManualMeterInputDialog(QDialog):
    """독립된 3개 계량장치의 11개 지침을 날짜별로 통합 입력/수정하는 팝업 창"""
    def __init__(self, default_date_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("독립 계량장치 일일 지침 수동 입력/수정")
        self.resize(550, 450)
        
        main_layout = QVBoxLayout()
        
        # 1. 날짜 선택 영역
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("<b>검침 대상 일자:</b>"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.fromString(default_date_str, "yyyy-MM-dd"))
        self.date_edit.dateChanged.connect(self.load_date_data) # 날짜 바꾸면 즉시 기존 데이터 로드
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        main_layout.addLayout(date_layout)
        
        # 2. 3대 장치 입력 폼 구성 (입력 필드 딕셔너리 정렬)
        self.inputs = {}
        grid = QGridLayout()
        
        # [그룹 1] 한전 메인 데이터
        group_main = QGroupBox("한전 메인 계량기")
        layout_main = QFormLayout()
        self.inputs["main_active"] = QLineEdit()
        self.inputs["main_reactive"] = QLineEdit()
        layout_main.addRow("메인 유효 전력량 (4번):", self.inputs["main_active"])
        layout_main.addRow("메인 무효 전력량 (5번):", self.inputs["main_reactive"])
        group_main.setLayout(layout_main)
        grid.addWidget(group_main, 0, 0)
        
        # [그룹 2] 산업용 전력 데이터
        group_ind = QGroupBox("산업용 (급수/정화조)")
        layout_ind = QFormLayout()
        self.inputs["ind_mid"] = QLineEdit()
        self.inputs["ind_max"] = QLineEdit()
        self.inputs["ind_light"] = QLineEdit()
        layout_ind.addRow("산업용 유효 중간 (13번):", self.inputs["ind_mid"])
        layout_ind.addRow("산업용 유효 최대 (14번):", self.inputs["ind_max"])
        layout_ind.addRow("산업용 유효 경부하 (15번):", self.inputs["ind_light"])
        group_ind.setLayout(layout_ind)
        grid.addWidget(group_ind, 0, 1)
        
        # [그룹 3] 가로등 전력 데이터
        group_street = QGroupBox("가로등 (LV10)")
        layout_street = QFormLayout()
        self.inputs["street_mid"] = QLineEdit()
        self.inputs["street_max"] = QLineEdit()
        self.inputs["street_light"] = QLineEdit()
        layout_street.addRow("가로등 유효 중간 (13번):", self.inputs["street_mid"])
        layout_street.addRow("가로등 유효 최대 (14번):", self.inputs["street_max"])
        layout_street.addRow("가로등 유효 경부하 (15번):", self.inputs["street_light"])
        group_street.setLayout(layout_street)
        grid.addWidget(group_street, 1, 0)
        
        # [그룹 4] 지열 시스템 데이터
        group_geo = QGroupBox("지열 시스템 지침")
        layout_geo = QFormLayout()
        self.inputs["geo_1"] = QLineEdit()
        self.inputs["geo_2"] = QLineEdit()
        self.inputs["geo_3"] = QLineEdit()
        layout_geo.addRow("지열 1호기 지침:", self.inputs["geo_1"])
        layout_geo.addRow("지열 2호기 지침:", self.inputs["geo_2"])
        layout_geo.addRow("지열 3호기 지침:", self.inputs["geo_3"])
        group_geo.setLayout(layout_geo)
        grid.addWidget(group_geo, 1, 1)
        
        main_layout.addLayout(grid)
        
        # 안내 문구
        lbl_info = QLabel("※ 숫자를 입력하면 실시간 저장/수정되며, 공백으로 두면 빈 데이터로 처리됩니다.")
        lbl_info.setStyleSheet("color: blue; font-size: 11px;")
        main_layout.addWidget(lbl_info)
        
        # 3. 저장 및 취소 버튼
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
        
        self.setLayout(main_layout)
        
        # 최초 실행 시 현재 설정된 날짜 데이터 로딩 가동
        self.load_date_data()
        
    def load_date_data(self):
        """날짜가 변경될 때마다 DB를 뒤져 해당 일자의 기존 수치를 양식에 표기합니다."""
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        # db_manager의 조회 함수 호출
        current_data = db_manager.get_manual_meter_data(date_str)
        
        for field, value in current_data.items():
            self.inputs[field].setText(value)
            
    def validate_and_accept(self):
        """입력된 값들이 정상적인 숫자 포맷인지 최종 무결성 검사를 수행합니다."""
        for field, edit in self.inputs.items():
            text = edit.text().strip()
            if text:
                try:
                    float(text)
                except ValueError:
                    QMessageBox.warning(self, "포맷 오류", "지침 입력 값은 순수 숫자(또는 소수점)만 입력 가능합니다.")
                    edit.setFocus()
                    return
        self.accept()

    def get_final_inputs(self):
        """저장 승인 시 가공된 날짜 및 11개 필드 딕셔너리를 메인 윈도우로 반환합니다."""
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        data_dict = {field: edit.text().strip() for field, edit in self.inputs.items()}
        return date_str, data_dict

class SCADAWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(10000) 
        self.last_hour = datetime.now().hour

    def initUI(self):
        self.setWindowTitle("변전실 데이터 통합 관리 시스템 (모듈화 프로젝트)")
        self.resize(1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        top_ctrl = QGroupBox("운영 제어 센터")
        top_layout = QHBoxLayout(top_ctrl)
        
        self.qdate = QDateEdit(QDate.currentDate())
        self.qdate.setCalendarPopup(True)
        top_layout.addWidget(QLabel("선택 날짜:"))
        top_layout.addWidget(self.qdate)
        
        self.btn_show_table = QPushButton("종합 데이터 표")
        self.btn_show_graph = QPushButton("부하 변동 그래프")
        self.btn_export_excel = QPushButton("엑셀 운영일지 출력")
        self.btn_export_excel.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        
        # SCADAWindow 클래스의 initUI 또는 버튼 레이아웃 배치 구역에 추가
        self.btn_meter_input = QPushButton("전력량 입력") # 요청하신 버튼명 지정
        self.btn_meter_input.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; min-height: 35px;")
        self.btn_meter_input.clicked.connect(self.click_open_meter_popup)
        
        top_layout.addWidget(self.btn_show_table)
        top_layout.addWidget(self.btn_show_graph)
        top_layout.addWidget(self.btn_export_excel)
        # 🛠️ 수정한 부분: hbox 대신 top_layout 레이아웃 변수명을 정확하게 매칭
        top_layout.addWidget(self.btn_meter_input)    
        main_layout.addWidget(top_ctrl)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # 테이블 탭 구성
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

        splitter.addWidget(QLabel("● 실시간 계측 데이터 로그"))
        splitter.addWidget(self.raw_table)
        splitter.addWidget(QLabel("● 시간별 평균 전력 추이"))
        splitter.addWidget(self.avg_table)
        splitter.addWidget(QLabel("● 일일 최고(MAX) / 최저(MIN) 값 설비 통계"))
        splitter.addWidget(self.extreme_table)
        table_layout.addWidget(splitter)
        self.stack.addWidget(self.page_table)

        # 그래프 탭 구성
        self.page_graph = QWidget()
        graph_layout = QVBoxLayout(self.page_graph)
        graph_ctrl = QHBoxLayout()
        self.data_selector = QComboBox()
        self.data_selector.addItems(db_manager.DATA_LABELS)
        self.period_selector = QComboBox()
        self.period_selector.addItems(["일간 (실시간 데이터)", "주간 (시간별 평균)", "월간 (시간별 평균)"])
        
        graph_ctrl.addWidget(QLabel("시각화 필드:"))
        graph_ctrl.addWidget(self.data_selector)
        graph_ctrl.addWidget(QLabel("조회 기간:"))
        graph_ctrl.addWidget(self.period_selector)
        graph_layout.addLayout(graph_ctrl)

        self.canvas = FigureCanvas(Figure(figsize=(8, 5)))
        self.ax = self.canvas.figure.add_subplot(111)
        graph_layout.addWidget(self.canvas)
        self.stack.addWidget(self.page_graph)

        self.btn_show_table.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_show_graph.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        # 💡 분리해 둔 엑셀 엔진 모듈의 함수를 바로 호출합니다!
        self.btn_export_excel.clicked.connect(self.export_excel_click)
        
        self.qdate.dateChanged.connect(self.auto_refresh)
        self.data_selector.currentIndexChanged.connect(self.update_graph)
        self.period_selector.currentIndexChanged.connect(self.update_graph)

        self.load_data()

    def load_data(self):
        selected_date = self.qdate.date().toString("yyyy-MM-dd")
        db_manager.calculate_daily_extremes(selected_date)
        
        try:
            conn = sqlite3.connect(db_manager.DB_NAME)
            c = conn.cursor()
            
            query_raw = f"SELECT log_date, log_time, {', '.join([f'\"{n}\"' for n in db_manager.DATA_LABELS])} FROM raw_data WHERE log_date = ? ORDER BY log_time DESC LIMIT 50"
            c.execute(query_raw, (selected_date,))
            self.display_table(self.raw_table, c.fetchall())
            
            query_avg = f"SELECT log_date, log_time, {', '.join([f'\"{n}\"' for n in db_manager.DATA_LABELS])} FROM hourly_avg WHERE log_date = ? ORDER BY log_time ASC"
            c.execute(query_avg, (selected_date,))
            self.display_table(self.avg_table, c.fetchall())
            
            query_ext = f"SELECT log_date, extreme_type, {', '.join([f'\"{n}\"' for n in db_manager.DATA_LABELS])} FROM daily_extremes WHERE log_date = ? ORDER BY extreme_type DESC"
            c.execute(query_ext, (selected_date,))
            self.display_table(self.extreme_table, c.fetchall(), is_extreme=True)
            
            conn.close()
        except Exception as e:
            print(f"UI 로딩 실패: {e}")

    def update_graph(self):
        if self.stack.currentIndex() != 1: return
        target_col = self.data_selector.currentText()
        period = self.period_selector.currentText()
        selected_date = self.qdate.date().toPyDate()

        conn = sqlite3.connect(db_manager.DB_NAME)
        if "일간" in period:
            query = f'SELECT log_time, "{target_col}" FROM raw_data WHERE log_date = ? ORDER BY log_time ASC'
            params = (selected_date.strftime('%Y-%m-%d'),)
        else:
            days = 7 if "주간" in period else 30
            start_date = selected_date - timedelta(days=days)
            query = f'SELECT log_date || \' \' || SUBSTR(log_time,1,5) as dt, "{target_col}" FROM hourly_avg WHERE log_date BETWEEN ? AND ? ORDER BY log_date, log_time'
            params = (start_date.strftime('%Y-%m-%d'), selected_date.strftime('%Y-%m-%d'))

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        self.ax.clear()
        if not df.empty:
            x_col = 'log_time' if "일간" in period else 'dt'
            self.ax.plot(df[x_col], df[target_col], marker='o', markersize=2, color='blue')
            import matplotlib.ticker as ticker
            self.ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
            self.ax.set_title(f"[{target_col}] {period} 추이 분석")
            self.ax.grid(True, linestyle='--')
            self.canvas.figure.autofmt_xdate() 
        else:
            self.ax.text(0.5, 0.5, "데이터가 존재하지 않습니다.", ha='center')
        self.canvas.draw()

    def display_table(self, table, rows, is_extreme=False):
        table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                txt = f"{val:.1f}" if isinstance(val, float) else str(val)
                item = QTableWidgetItem(txt)
                if is_extreme and c_idx > 1:
                    if row[1] == 'MAX': item.setForeground(Qt.red)
                    elif row[1] == 'MIN': item.setForeground(Qt.blue)
                table.setItem(r_idx, c_idx, item)

    def export_excel_click(self):
        selected_date = self.qdate.date().toString("yyyy-MM-dd")
        try:
            excel_report.generate_excel_report(selected_date)
            QMessageBox.information(self, "출력 완료", f"[{selected_date}_전기실_운영일지.xlsx]가 생성되었습니다.")
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
        """'전력량 입력' 버튼 터치 시 수동 검침 통합 팝업을 기동하는 슬롯 함수"""
        # 현재 화면 캘린더에 지정되어 있는 날짜를 기본값으로 토스
        current_view_date = self.qdate.date().toString("yyyy-MM-dd")
        
        dialog = ManualMeterInputDialog(current_view_date, self)
        if dialog.exec_() == QDialog.Accepted:
            save_date, final_data = dialog.get_final_inputs()
            try:
                # db_manager에 설계한 통합 저장 로직 원격 작동
                db_manager.save_manual_meter_data(save_date, final_data)
                
                QMessageBox.information(
                    self, "입력 및 수정 완료", 
                    f"[{save_date}] 일자의 독립 계량기 11개 필드 지침 데이터가\nDB(manual_meter_logs)에 안전하게 반영되었습니다."
                )
                
                # 필요 시 메인 화면 테이블 리프레시 가동
                if hasattr(self, 'refresh_data'):
                    self.refresh_data()
                    
            except Exception as e:
                QMessageBox.critical(self, "저장 실패", f"DB 수동 데이터 업데이트 프로세스 중 오류 발생:\n{e}")

if __name__ == "__main__":
    db_manager.init_db()
    t = threading.Thread(target=plc_worker.serial_receive_thread, daemon=True)
    t.start()
    
    app = QApplication(sys.argv)
    win = SCADAWindow()
    win.show()
    sys.exit(app.exec_())