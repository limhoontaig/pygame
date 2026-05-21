import sys
import threading
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, QLabel, QHBoxLayout, 
                             QDateEdit, QComboBox, QGroupBox, QSplitter, QStackedWidget, QMessageBox)
from PyQt5.QtCore import QTimer, QDate, Qt

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# 💡 직접 만든 커스텀 기능 모듈들을 가져옵니다!
import db_manager
import plc_worker
import excel_report

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
        
        top_layout.addWidget(self.btn_show_table)
        top_layout.addWidget(self.btn_show_graph)
        top_layout.addWidget(self.btn_export_excel)
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

if __name__ == "__main__":
    db_manager.init_db()
    t = threading.Thread(target=plc_worker.serial_receive_thread, daemon=True)
    t.start()
    
    app = QApplication(sys.argv)
    win = SCADAWindow()
    win.show()
    sys.exit(app.exec_())