import sys
import serial
import threading
import sqlite3
import struct
import time
import pandas as pd
from datetime import datetime, timedelta

# QStackedWidget이 여기서 누락되어 에러가 났던 것입니다. 추가했습니다.
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, QLabel, QHBoxLayout, 
                             QDateEdit, QTimeEdit, QComboBox, QGridLayout, QGroupBox, QSplitter,
                             QStackedWidget)
from PyQt5.QtCore import QTimer, QDate, QTime, Qt

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# ==========================================
# 1. 통신 및 데이터 설정 (PLC D900~D915 대응)
# ==========================================
COM_PORT = 'COM3'         # 실제 연결된 포트번호 확인 (예: COM3, COM6)
BAUD_RATE = 19200         # PLC 설정과 동일하게 (19200)
MY_SLAVE_ID = 5           # PLC P2P 설정의 대상 국번
NUM_WORDS = 16            # D900 ~ D915 (총 16개 워드)
DB_NAME = "plc_logging_real.db"

# 컬럼 라벨 정의 (D900 ~ D915)
# 사용하시는 환경에 맞게 이름을 수정하세요.
# COLUMN_LABELS = ["시간"] + [f"D{900+i}" for i in range(NUM_WORDS)]
# ==========================================
# 컬럼 라벨 정의 (D100 ~ D113)
# ==========================================
# D100-D101: 실내온도, 외기온도, SF 운전시간, EF 운전시간 (4개)
# D102-D119: 변압기1-5 (전압, 전류, 전력, 온도 × 3대 = 12개)
COLUMN_LABELS = ["날짜", "시간", "실내온도", "외기온도", "SF운전시간", "EF운전시간",
                 "변압기1전압", "변압기1전류", "변압기1전력", "변압기1온도",
                 "변압기2전압", "변압기2전류", "변압기2전력", "변압기2온도",
                 "변압기3전압", "변압기3전류", "변압기3전력", "변압기3온도"]

# ==========================================
# 2. 유틸리티 함수 (CRC 및 DB)
# ==========================================
def calculate_crc(data):
    """Modbus RTU CRC-16 계산"""
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
    """수신 데이터의 CRC 검증 (표준 및 바이트 반전 모두 대응)"""
    if len(data) < 4: return False
    body = data[:-2]
    recv_crc = data[-2:]
    calc_crc = calculate_crc(body)
    return recv_crc == calc_crc or recv_crc == calc_crc[::-1]

def init_db():
    """데이터베이스 및 테이블 초기화 (날짜/시간 분리 버전)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # D900~D915 컬럼 생성 (REAL 타입)
    cols = ", ".join([f"D{900+i} REAL" for i in range(NUM_WORDS)])
    
    # 1. 원데이터 테이블 (log_date, log_time 분리)
    c.execute(f"CREATE TABLE IF NOT EXISTS raw_data (log_date DATE, log_time TIME, {cols})")
    
    # 2. 평균 데이터 테이블 (log_date, log_time 분리)
    c.execute(f"CREATE TABLE IF NOT EXISTS hourly_avg (log_date DATE, log_time TIME, {cols})")
    
    conn.commit()
    conn.close()

def insert_raw_data(values):
    """실시간 수신 데이터 가공 및 저장 (10으로 나누기 반영)"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        now = datetime.now()
        l_date = now.strftime('%Y-%m-%d')
        l_time = now.strftime('%H:%M:%S')
        
        # PLC에서 10배 곱해져 온 정수를 다시 10.0으로 나누어 소수점 생성
        # 모든 값을 일단 실수형으로 변환하며 10으로 나눕니다.
        adjusted_values = [] 
        for i, v in enumerate(values):
            if i <4:
                adjusted_values.append(v / 10.0)
            elif i in [7, 11, 15]: # 전류는 100으로 나눔
                adjusted_values.append(v / 10.0)  
            else:
                adjusted_values.append (float(v))

        # 32개 워드(16개 REAL) 혹은 16개 정수 수량에 맞게 조정
        placeholders = ", ".join(["?"] * len(adjusted_values))
        col_names = ", ".join([f"D{900+i}" for i in range(len(adjusted_values))])
        
        query = f"INSERT INTO raw_data (log_date, log_time, {col_names}) VALUES (?, ?, {placeholders})"
        c.execute(query, [l_date, l_time] + adjusted_values)
        
        conn.commit()
        conn.close()
        print(f"[{l_date} {l_time}] 저장 완료: {adjusted_values}")
    except Exception as e:
        print(f"DB 저장 오류: {e}")

# ==========================================
# 3. 시리얼 수신 엔진 (핵심 수정 부분)
# ==========================================
def serial_receive_thread():
    try:
        ser = serial.Serial(port=COM_PORT, baudrate=BAUD_RATE, timeout=0.1)
        print(f"통신 시작: {COM_PORT} @ {BAUD_RATE}")
    except Exception as e:
        print(f"포트 열기 실패: {e}")
        return

    buffer = b""
    while True:
        try:
            if ser.in_waiting > 0:
                buffer += ser.read(ser.in_waiting)
                
                # 프레임 동기화: Slave ID(5)를 찾음
                while len(buffer) >= 8:
                    if buffer[0] != MY_SLAVE_ID:
                        buffer = buffer[1:]
                        continue
                    
                    func_code = buffer[1]
                    # 0x10 (Write Multi) 처리
                    if func_code == 0x10:
                        # PLC 송신 구조: [5][10][Addr2][Cnt2][Byte1][Data32][CRC2] = 총 41바이트
                        expected_len = 41 
                        if len(buffer) < expected_len: break # 데이터 더 기다림
                        
                        packet = buffer[:expected_len]
                        buffer = buffer[expected_len:]
                        
                        if verify_crc(packet):
                            # 데이터 파싱 (D900~D915) - Big Endian(>h)으로 읽음
                            raw_values = packet[7:39] # 데이터 시작 위치
                            values = struct.unpack(f'>16h', raw_values)
                            insert_raw_data(values)
                        else:
                            # CRC 오류 발생 시 HEX 값 출력
                            # ' '.join(...)을 사용하면 05 10 00... 처럼 바이트 사이에 공백을 넣어 가독성이 좋아집니다.
                            hex_data = ' '.join([f'{b:02X}' for b in packet])
                            with open("comm_error_log.txt", "a") as f:
                                f.write(f"[{datetime.now()}] CRC Error: {hex_data}\n")
                            print(f"CRC 오류 데이터 로그 저장됨: {hex_data}")
                            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CRC 오류 발생!")
                            print(f"수신된 HEX 데이터: {hex_data}")
                            # 필요하다면 파일로 로그를 남길 수도 있습니다.
                    else:
                        buffer = buffer[1:] # 알 수 없는 기능코드 버림
            time.sleep(0.01)
        except Exception as e:
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), f"수신 루프 에러: {e}")
            break

# ==========================================
# 4. 시간당 평균 계산 로직
# ==========================================
def calculate_hourly_avg():
    print("평균 계산 함수 시작됨!") # 이 메시지가 출력되는지 확인하세요

    try:
        conn = sqlite3.connect(DB_NAME, timeout=30) # 잠금 대기 시간 늘림
        conn.execute("PRAGMA journal_mode = WAL") # WAL 모드로 변경하여 동시 읽기/쓰기 허용 
        c = conn.cursor()
        
        now = datetime.now()
        last_hour = (now - timedelta(hours=1))
        target_date = last_hour.strftime('%Y-%m-%d')
        target_hour = last_hour.strftime('%H')
        
        avg_select = ", ".join([f"AVG(D{900+i})" for i in range(NUM_WORDS)])
        col_names = ", ".join([f"D{900+i}" for i in range(NUM_WORDS)])
        
        # log_date와 log_time(시간대)으로 필터링
        query = f"SELECT {avg_select} FROM raw_data WHERE log_date = ? AND log_time LIKE ?"
        c.execute(query, (target_date, f"{target_hour}:%"))
        result = c.fetchone()

        if result and result[0] is not None:
            # [수정 부분] 결과값을 소수점 첫째 자리까지 반올림
            # round(값, 1) -> 소수점 첫째 자리까지 남김
            rounded_result = [round(val, 1) for val in result]
            
            target_date = last_hour.strftime('%Y-%m-%d')
            placeholders = ", ".join(["?"] * NUM_WORDS)
            col_names = ", ".join([f"D{900+i}" for i in range(NUM_WORDS)])

            insert_query = f"INSERT INTO hourly_avg (log_date, log_time, {col_names}) VALUES (?, ?, {placeholders})"
            # rounded_result를 저장함
            c.execute(insert_query, [target_date, f"{last_hour.strftime('%H')}:00:00"] + rounded_result)
            conn.commit()
    except sqlite3.OperationalError as e:
            print(f"DB 잠김 오류 발생: {e}") # 여기서 에러를 잡아낼 수 있습니다.
    finally:
        conn.close()

# ==========================================
# 5. GUI 클래스 (PyQt5)
# ==========================================
class SCADAWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(10000) # 10초마다 화면 갱신
        self.last_hour = datetime.now().hour

    def initUI(self):
        self.setWindowTitle("LS PLC D900-D915 Data Logger")
        self.resize(1100, 700)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 검색 영역
        search_box = QGroupBox("검색 설정")
        grid = QGridLayout(search_box)
        self.qdate = QDateEdit(QDate.currentDate())
        grid.addWidget(QLabel("조회 날짜:"), 0, 0)
        grid.addWidget(self.qdate, 0, 1)
        btn = QPushButton("데이터 조회")
        btn.clicked.connect(self.load_data)
        grid.addWidget(btn, 0, 2)
        layout.addWidget(search_box)

        # 테이블 영역
        splitter = QSplitter(Qt.Vertical)
        self.raw_table = QTableWidget()
        self.raw_table.setColumnCount(NUM_WORDS + 1)
        self.raw_table.setHorizontalHeaderLabels(COLUMN_LABELS)
        
        self.avg_table = QTableWidget()
        self.avg_table.setColumnCount(NUM_WORDS + 1)
        self.avg_table.setHorizontalHeaderLabels(COLUMN_LABELS)

        splitter.addWidget(QLabel("● 실시간 수신 데이터 (Raw Data)"))
        splitter.addWidget(self.raw_table)
        splitter.addWidget(QLabel("● 시간별 평균 데이터 (Hourly Average)"))
        splitter.addWidget(self.avg_table)
        layout.addWidget(splitter)

    def load_data(self):
        date_str = self.qdate.date().toString("yyyy-MM-dd")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # [수정 전] c.execute("SELECT * FROM raw_data WHERE timestamp LIKE ? ...")
        # [수정 후] log_date 컬럼을 기준으로 조회하도록 변경
        try:
            # Raw Data 조회 (log_date가 선택한 날짜와 일치하는 데이터)
            c.execute("SELECT * FROM raw_data WHERE log_date = ? ORDER BY log_time DESC LIMIT 50", (date_str,))
            raw_rows = c.fetchall()
            self.display_table(self.raw_table, raw_rows)

            # Average Data 조회
            c.execute("SELECT * FROM hourly_avg WHERE log_date = ? ORDER BY log_time DESC", (date_str,))
            avg_rows = c.fetchall()
            self.display_table(self.avg_table, avg_rows)
            
        except sqlite3.OperationalError as e:
            print(f"조회 오류 발생: {e}")
            print("기존 DB 파일과 새로운 코드의 구조가 맞지 않습니다. 'plc_logging_real.db' 파일을 삭제하고 다시 실행하세요.")
        
        conn.close()

    def display_table(self, table, rows):
        table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                item = QTableWidgetItem(f"{val:.2f}" if isinstance(val, float) else str(val))
                table.setItem(r_idx, c_idx, item)

    def auto_refresh(self):
        curr_hour = datetime.now().hour
        if curr_hour != self.last_hour:
            calculate_hourly_avg()
            self.last_hour = curr_hour
        self.load_data()

# ==========================================
# 2. 메인 윈도우 클래스
# ==========================================


class SCADAWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(10000) # 10초마다 갱신
        self.last_hour = datetime.now().hour

    def initUI(self):
        self.setWindowTitle("변전실 데이터 모니터링 시스템")
        self.resize(1200, 850)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 상단 공통 제어 바
        top_ctrl = QGroupBox("조회 설정")
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

        # 화면 전환용 스택 위젯
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # --- 페이지 1: 데이터 테이블 (검색 화면) ---
        self.page_table = QWidget()
        table_layout = QVBoxLayout(self.page_table)
        splitter = QSplitter(Qt.Vertical)
        
        self.raw_table = QTableWidget()
        self.raw_table.setColumnCount(len(COLUMN_LABELS))
        self.raw_table.setHorizontalHeaderLabels(COLUMN_LABELS)
        
        self.avg_table = QTableWidget()
        self.avg_table.setColumnCount(len(COLUMN_LABELS))
        self.avg_table.setHorizontalHeaderLabels(COLUMN_LABELS)

        splitter.addWidget(QLabel("● 실시간 로그 (1분 단위)"))
        splitter.addWidget(self.raw_table)
        splitter.addWidget(QLabel("● 시간별 평균 데이터"))
        splitter.addWidget(self.avg_table)
        table_layout.addWidget(splitter)
        self.stack.addWidget(self.page_table)

        # --- 페이지 2: 그래프 분석 화면 ---
        self.page_graph = QWidget()
        graph_layout = QVBoxLayout(self.page_graph)
        
        graph_ctrl = QHBoxLayout()
        self.data_selector = QComboBox()
        self.data_selector.addItems([f"D{900+i}" for i in range(NUM_WORDS)])
        self.period_selector = QComboBox()
        self.period_selector.addItems(["일간 (실시간)", "주간 (평균)", "월간 (평균)"])
        
        graph_ctrl.addWidget(QLabel("분석 항목:"))
        graph_ctrl.addWidget(self.data_selector)
        graph_ctrl.addWidget(QLabel("기간:"))
        graph_ctrl.addWidget(self.period_selector)
        graph_layout.addLayout(graph_ctrl)

        self.canvas = FigureCanvas(Figure(figsize=(8, 5)))
        self.ax = self.canvas.figure.add_subplot(111)
        graph_layout.addWidget(self.canvas)
        self.stack.addWidget(self.page_graph)

        # 버튼 이벤트 연결
        self.btn_show_table.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_show_graph.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        # 설정 변경 시 자동 업데이트
        self.qdate.dateChanged.connect(self.auto_refresh)
        self.data_selector.currentIndexChanged.connect(self.update_graph)
        self.period_selector.currentIndexChanged.connect(self.update_graph)

        self.load_data()

    def load_data(self):
        date_str = self.qdate.date().toString("yyyy-MM-dd")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("SELECT * FROM raw_data WHERE log_date = ? ORDER BY log_time DESC LIMIT 50", (date_str,))
            self.display_table(self.raw_table, c.fetchall())
            c.execute("SELECT * FROM hourly_avg WHERE log_date = ? ORDER BY log_time DESC", (date_str,))
            self.display_table(self.avg_table, c.fetchall())
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
            query = f"SELECT log_time, {target_col} FROM raw_data WHERE log_date = ? ORDER BY log_time ASC"
            params = (selected_date.strftime('%Y-%m-%d'),)
        else:
            days = 7 if "주간" in period else 30
            start_date = selected_date - timedelta(days=days)
            query = f"""SELECT log_date || ' ' || SUBSTR(log_time,1,5) as dt, {target_col} 
                        FROM hourly_avg WHERE log_date BETWEEN ? AND ? ORDER BY log_date, log_time"""
            params = (start_date.strftime('%Y-%m-%d'), selected_date.strftime('%Y-%m-%d'))

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        self.ax.clear()
        if not df.empty:
            x_col = 'log_time' if "일간" in period else 'dt'
            self.ax.plot(df[x_col], df[target_col], marker='o', markersize=2, color='blue', linestyle='-')
            
            # --- X축 눈금 최적화 부분 ---
            import matplotlib.ticker as ticker
            
            # 전체 데이터 중 약 10개 내외의 눈금만 표시하도록 설정
            # MaxNLocator는 데이터 양에 맞춰 적절한 간격으로 최대 10개의 라벨을 선택합니다.
            self.ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
            
            # 만약 월간(30일) 데이터에서 정확히 3일 간격을 선호하신다면 아래와 같이 수동 설정도 가능합니다.
            # ticks = df[x_col].values
            # self.ax.set_xticks(ticks[::len(ticks)//10 if len(ticks) > 10 else 1])
            
            self.ax.set_title(f"{target_col} {period} 추이")
            self.ax.grid(True, linestyle='--', alpha=0.7)
            self.canvas.figure.autofmt_xdate() # 날짜 기울여서 표시
        else:
            self.ax.text(0.5, 0.5, "데이터가 없습니다.", ha='center')
        
        self.canvas.draw()

    def display_table(self, table, rows):
        table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                txt = f"{val:.1f}" if isinstance(val, float) else str(val)
                table.setItem(r_idx, c_idx, QTableWidgetItem(txt))

    def auto_refresh(self):
        self.load_data()
        self.update_graph()

# ==========================================
# 메인 실행
# ==========================================
if __name__ == "__main__":
    init_db()
    # 수신 스레드 실행
    t = threading.Thread(target=serial_receive_thread, daemon=True)
    t.start()
    
    app = QApplication(sys.argv)
    win = SCADAWindow()
    win.show()
    sys.exit(app.exec_())