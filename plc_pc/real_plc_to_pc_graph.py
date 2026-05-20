import sys
import serial
import threading
import sqlite3
import struct
import time
import pandas as pd
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, QLabel, QHBoxLayout, 
                             QDateEdit, QComboBox, QGroupBox, QSplitter, QStackedWidget)
from PyQt5.QtCore import QTimer, QDate, Qt

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. 통신 및 데이터 설정 (주파수를 전력 앞으로 배치 -> 총 50개 워드)
# ==========================================
COM_PORT = 'COM3'         
BAUD_RATE = 19200         
MY_SLAVE_ID = 5           
NUM_WORDS = 50            # 32비트 전력량이 2워드를 차지하므로 총 50워드 유지
DB_NAME = "plc_logging_real.db"

# 데이터 레이블 (주파수를 KEP_P_kW 앞으로 이동 완료)
DATA_LABELS = [
    "실내온도", "외기온도", "SF운전시간", "EF운전시간",
    "KEP_A_R", "KEP_A_S", "KEP_A_T", 
    "KEP_V_R", "KEP_V_S", "KEP_V_T", "KEP_V_R_S", "KEP_V_S_T", "KEP_V_T_R", 
    "KEP_frequency",  # <-- 요청하신 대로 KEP_P_kW 앞으로 배치 (인덱스 13번)
    "KEP_P_kW",       # (인덱스 14번)
    "KEP_P_mWh",      # 32비트 Int 처리 (인덱스 15번)
    "Tr1_A_R", "Tr1_A_S", "Tr1_A_T", "Tr1_V_R", "Tr1_V_S", "Tr1_V_T", "Tr1_V_R_S", "Tr1_V_S_T", "Tr1_V_T_R", "Tr1_P_kW", "Tr1_Temp",
    "Tr2_A_R", "Tr2_A_S", "Tr2_A_T", "Tr2_V_R", "Tr2_V_S", "Tr2_V_T", "Tr2_V_R_S", "Tr2_V_S_T", "Tr2_V_T_R", "Tr2_P_kW", "Tr2_Temp",
    "Tr3_A_R", "Tr3_A_S", "Tr3_A_T", "Tr3_V_R", "Tr3_V_S", "Tr3_V_T", "Tr3_V_R_S", "Tr3_V_S_T", "Tr3_V_T_R", "Tr3_P_kW", "Tr3_Temp"
]

COLUMN_LABELS = ["날짜", "시간/구분"] + DATA_LABELS

# ==========================================
# 2. 유틸리티 및 데이터베이스 함수
# ==========================================
def calculate_crc(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack('<H', crc)

def verify_crc(data):
    if len(data) < 4: return False
    body = data[:-2]
    recv_crc = data[-2:]
    calc_crc = calculate_crc(body)
    return recv_crc == calc_crc or recv_crc == calc_crc[::-1]

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    cols = ", ".join([f'"{name}" REAL' for name in DATA_LABELS])
    
    c.execute(f'CREATE TABLE IF NOT EXISTS raw_data (log_date DATE, log_time TIME, {cols})')
    c.execute(f'CREATE TABLE IF NOT EXISTS hourly_avg (log_date DATE, log_time TIME, {cols})')
    c.execute(f'''CREATE TABLE IF NOT EXISTS daily_extremes (
                    log_date DATE, extreme_type TEXT, {cols}, PRIMARY KEY (log_date, extreme_type))''')
    conn.commit()
    conn.close()

def insert_raw_data(values):
    """위치 변경 및 32비트 조합이 완료된 49개 값을 가공하여 저장"""
    if len(values) < len(DATA_LABELS):
        return
        
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        now = datetime.now()
        l_date = now.strftime('%Y-%m-%d')
        l_time = now.strftime('%H:%M:%S')
        
        adjusted_values = []
        for i, v in enumerate(values):
            # 1. 10으로 나누는 항목 (0~6번 필드 + 위치 이동한 13번 주파수 필드 포함)
            if i in [0, 1, 2, 3, 4, 5, 6, 13]:  # 주파수 인덱스가 13번으로 변경됨
                adjusted_values.append(v / 10.0)
            # 변압기 온도 피드백 (인덱스 유지: 27, 38, 49번)
            elif i in [27, 38, 49]:         
                adjusted_values.append(v / 10.0)
                
            # 2. 100으로 나누는 항목
            elif i in [7, 8, 9, 10, 11, 12]:   # KEP_V 계열 전압
                adjusted_values.append(v / 100.0)
            elif i == 15:                     # KEP_P_mWh (32비트 전력량 인덱스가 15번이 됨)
                adjusted_values.append(v / 100.0)
                
            # 3. 정수 형태 유지 (KEP_P_kW는 14번 정수형태 유지)
            else:
                adjusted_values.append(float(v))

        placeholders = ", ".join(["?"] * len(adjusted_values))
        col_names = ", ".join([f'"{name}"' for name in DATA_LABELS])
        
        query = f"INSERT INTO raw_data (log_date, log_time, {col_names}) VALUES (?, ?, {placeholders})"
        c.execute(query, [l_date, l_time] + adjusted_values)
        conn.commit()
        conn.close()
        print(f"[{l_date} {l_time}] DB 저장 성공 (주파수 정렬 완료)")
    except Exception as e:
        print(f"DB 저장 오류: {e}")

# ==========================================
# 3. 데이터 분석 연산부
# ==========================================
def calculate_hourly_avg():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=30)
        c = conn.cursor()
        now = datetime.now()
        last_hour = (now - timedelta(hours=1))
        target_date = last_hour.strftime('%Y-%m-%d')
        target_hour = last_hour.strftime('%H')
        
        avg_select = ", ".join([f'AVG("{name}")' for name in DATA_LABELS])
        col_names = ", ".join([f'"{name}"' for name in DATA_LABELS])
        
        query = f"SELECT {avg_select} FROM raw_data WHERE log_date = ? AND log_time LIKE ?"
        c.execute(query, (target_date, f"{target_hour}:%"))
        result = c.fetchone()

        if result and result[0] is not None:
            rounded_result = [round(val, 1) for val in result]
            placeholders = ", ".join(["?"] * len(DATA_LABELS))
            insert_query = f"INSERT INTO hourly_avg (log_date, log_time, {col_names}) VALUES (?, ?, {placeholders})"
            c.execute(insert_query, [target_date, f"{target_hour}:00:00"] + rounded_result)
            conn.commit()
    except Exception as e:
        print(f"평균 계산 오류: {e}")
    finally:
        conn.close()

def calculate_daily_extremes(target_date):
    try:
        conn = sqlite3.connect(DB_NAME, timeout=30)
        c = conn.cursor()
        max_select = ", ".join([f'MAX("{name}")' for name in DATA_LABELS])
        min_select = ", ".join([f'MIN("{name}")' for name in DATA_LABELS])
        col_names = ", ".join([f'"{name}"' for name in DATA_LABELS])
        placeholders = ", ".join(["?"] * len(DATA_LABELS))
        
        c.execute(f'SELECT {max_select} FROM raw_data WHERE log_date = ?', (target_date,))
        max_res = c.fetchone()
        if max_res and max_res[0] is not None:
            c.execute(f'INSERT OR REPLACE INTO daily_extremes (log_date, extreme_type, {col_names}) VALUES (?, ?, {placeholders})',
                      [target_date, 'MAX'] + list(max_res))
            
        c.execute(f'SELECT {min_select} FROM raw_data WHERE log_date = ?', (target_date,))
        min_res = c.fetchone()
        if min_res and min_res[0] is not None:
            c.execute(f'INSERT OR REPLACE INTO daily_extremes (log_date, extreme_type, {col_names}) VALUES (?, ?, {placeholders})',
                      [target_date, 'MIN'] + list(min_res))
        conn.commit()
    except Exception as e:
        print(f"최고/최저 계산 오류: {e}")
    finally:
        conn.close()

# ==========================================
# 4. 정밀 시리얼 수신 엔진
# ==========================================
def serial_receive_thread():
    try:
        ser = serial.Serial(port=COM_PORT, baudrate=BAUD_RATE, timeout=0.1)
        print(f"통신 엔진 가동 완료: {COM_PORT} @ {BAUD_RATE}")
    except Exception as e:
        print(f"시리얼 포트 개방 실패: {e}")
        return

    buffer = b""
    while True:
        try:
            if ser.in_waiting > 0:
                buffer += ser.read(ser.in_waiting)
                
                while len(buffer) >= 7:
                    if buffer[0] != MY_SLAVE_ID:
                        buffer = buffer[1:]
                        continue
                    
                    func_code = buffer[1]
                    if func_code == 0x10:
                        expected_len = 7 + (NUM_WORDS * 2) + 2 
                        
                        if len(buffer) < expected_len: 
                            break 
                        
                        packet = buffer[:expected_len]
                        
                        if verify_crc(packet):
                            raw_values = packet[7:7+(NUM_WORDS * 2)]
                            
                            # [구조 매핑 개편]
                            # 15개 항목 (실내온도~KEP_P_kW까지 15개의 16비트 정수) + 32비트 전력량(i) + 나머지 33개(33h)
                            # 형식 문자열 기호 설명: >15h (15개 short) + i (1개 int) + 33h (33개 short) = 총 49개 데이터 반환
                            values = struct.unpack('>15h i 33h', raw_values)
                            insert_raw_data(values)
                            
                            buffer = buffer[expected_len:] 
                        else:
                            buffer = buffer[1:]
                    else:
                        buffer = buffer[1:]
            time.sleep(0.01)
        except Exception as e:
            print(f"시리얼 수신 스레드 예외 발생: {e}")
            break

# ==========================================
# 5. GUI 메인 윈도우 클래스 (PyQt5)
# ==========================================
class SCADAWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(10000) 
        self.last_hour = datetime.now().hour

    def initUI(self):
        self.setWindowTitle("변전실 데이터 통합 모니터링 시스템 (주파수 재정렬 버전)")
        self.resize(1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        top_ctrl = QGroupBox("조회 및 화면 설정")
        top_layout = QHBoxLayout(top_ctrl)
        
        self.qdate = QDateEdit(QDate.currentDate())
        self.qdate.setCalendarPopup(True)
        top_layout.addWidget(QLabel("날짜 선택:"))
        top_layout.addWidget(self.qdate)
        
        self.btn_show_table = QPushButton("데이터 표 보기")
        self.btn_show_graph = QPushButton("분석 그래프 보기")
        top_layout.addWidget(self.btn_show_table)
        top_layout.addWidget(self.btn_show_graph)
        main_layout.addWidget(top_ctrl)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # 페이지 1: 테이블 화면
        self.page_table = QWidget()
        table_layout = QVBoxLayout(self.page_table)
        splitter = QSplitter(Qt.Vertical)
        
        self.raw_table = QTableWidget()
        self.raw_table.setColumnCount(len(COLUMN_LABELS))
        self.raw_table.setHorizontalHeaderLabels(COLUMN_LABELS)
        
        self.avg_table = QTableWidget()
        self.avg_table.setColumnCount(len(COLUMN_LABELS))
        self.avg_table.setHorizontalHeaderLabels(COLUMN_LABELS)

        self.extreme_table = QTableWidget()
        self.extreme_table.setColumnCount(len(COLUMN_LABELS))
        self.extreme_table.setHorizontalHeaderLabels(COLUMN_LABELS)

        splitter.addWidget(QLabel("● 실시간 로그 (최근 50개 항목)"))
        splitter.addWidget(self.raw_table)
        splitter.addWidget(QLabel("● 시간별 평균 데이터 추이"))
        splitter.addWidget(self.avg_table)
        splitter.addWidget(QLabel("● 일일 최고(MAX) / 최저(MIN) 값 요약 정보"))
        splitter.addWidget(self.extreme_table)
        
        table_layout.addWidget(splitter)
        self.stack.addWidget(self.page_table)

        # 페이지 2: 그래프 화면
        self.page_graph = QWidget()
        graph_layout = QVBoxLayout(self.page_graph)
        
        graph_ctrl = QHBoxLayout()
        self.data_selector = QComboBox()
        self.data_selector.addItems(DATA_LABELS)
        self.period_selector = QComboBox()
        self.period_selector.addItems(["일간 (실시간 데이터)", "주간 (시간별 평균)", "월간 (시간별 평균)"])
        
        graph_ctrl.addWidget(QLabel("분석 및 시각화 항목:"))
        graph_ctrl.addWidget(self.data_selector)
        graph_ctrl.addWidget(QLabel("분석 기간:"))
        graph_ctrl.addWidget(self.period_selector)
        graph_layout.addLayout(graph_ctrl)

        self.canvas = FigureCanvas(Figure(figsize=(8, 5)))
        self.ax = self.canvas.figure.add_subplot(111)
        graph_layout.addWidget(self.canvas)
        self.stack.addWidget(self.page_graph)

        self.btn_show_table.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_show_graph.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        self.qdate.dateChanged.connect(self.auto_refresh)
        self.data_selector.currentIndexChanged.connect(self.update_graph)
        self.period_selector.currentIndexChanged.connect(self.update_graph)

        self.load_data()

    def load_data(self):
        date_str = self.qdate.date().toString("yyyy-MM-dd")
        calculate_daily_extremes(date_str)
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("SELECT * FROM raw_data WHERE log_date = ? ORDER BY log_time DESC LIMIT 50", (date_str,))
            self.display_table(self.raw_table, c.fetchall())
            
            c.execute("SELECT * FROM hourly_avg WHERE log_date = ? ORDER BY log_time DESC", (date_str,))
            self.display_table(self.avg_table, c.fetchall())
            
            c.execute("SELECT * FROM daily_extremes WHERE log_date = ? ORDER BY extreme_type DESC", (date_str,))
            self.display_table(self.extreme_table, c.fetchall(), is_extreme=True)
        except Exception as e:
            print(f"조회 오류: {e}")
        conn.close()

    def update_graph(self):
        if self.stack.currentIndex() != 1: return
        
        target_col = self.data_selector.currentText()
        period = self.period_selector.currentText()
        selected_date = self.qdate.date().toPyDate()

        conn = sqlite3.connect(DB_NAME)
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
            self.ax.plot(df[x_col], df[target_col], marker='o', markersize=2, color='blue', linestyle='-')
            
            import matplotlib.ticker as ticker
            self.ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
            
            self.ax.set_title(f"[{target_col}] {period} 데이터 추이 분석")
            self.ax.grid(True, linestyle='--', alpha=0.7)
            self.canvas.figure.autofmt_xdate() 
        else:
            self.ax.text(0.5, 0.5, "해당 기간의 데이터가 존재하지 않습니다.", ha='center')
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

    def auto_refresh(self):
        curr_hour = datetime.now().hour
        if curr_hour != self.last_hour:
            calculate_hourly_avg()
            self.last_hour = curr_hour
        self.load_data()
        self.update_graph()

# ==========================================
# 6. 메인 실행부
# ==========================================
if __name__ == "__main__":
    init_db()
    
    t = threading.Thread(target=serial_receive_thread, daemon=True)
    t.start()
    
    app = QApplication(sys.argv)
    win = SCADAWindow()
    win.show()
    sys.exit(app.exec_())