import sys
import serial
import threading
import sqlite3
import struct
import time
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, QLabel, QHBoxLayout,
                             QDateEdit, QTimeEdit, QGroupBox, QSplitter, QGridLayout)
from PyQt5.QtCore import QTimer, QDate, QTime, Qt

# ==========================================
# 1. 통신 및 데이터 설정 (PLC D900~D915 대응)
# ==========================================
COM_PORT = 'COM3'         # 실제 연결된 포트번호 확인 (예: COM3, COM6)
BAUD_RATE = 19200         # PLC 설정과 동일하게 (19200)
MY_SLAVE_ID = 5           # PLC P2P 설정의 대상 국번
NUM_WORDS = 16            # D900 ~ D915 (총 16개 워드)
DB_NAME = "plc_logging.db"

# 컬럼 라벨 정의 (D900 ~ D915)
# 사용하시는 환경에 맞게 이름을 수정하세요.
# COLUMN_LABELS = ["시간"] + [f"D{900+i}" for i in range(NUM_WORDS)]
COLUMN_LABELS = ["시간", "실내온도", "외기온도", "SF 운전시간", "EF 운전시간",       
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
    """데이터베이스 및 테이블 초기화"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # D900~D915 컬럼 생성
    cols = ", ".join([f"D{900+i} REAL" for i in range(NUM_WORDS)])
    c.execute(f"CREATE TABLE IF NOT EXISTS raw_data (timestamp DATETIME, {cols})")
    c.execute(f"CREATE TABLE IF NOT EXISTS hourly_avg (timestamp DATETIME, {cols})")
    conn.commit()
    conn.close()

def insert_raw_data(values):
    """실시간 수신 데이터 저장"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        placeholders = ", ".join(["?"] * NUM_WORDS)
        col_names = ", ".join([f"D{900+i}" for i in range(NUM_WORDS)])
        c.execute(f"INSERT INTO raw_data (timestamp, {col_names}) VALUES (?, {placeholders})", [now] + list(values))
        conn.commit()
        conn.close()
        print(f"[{now}] 데이터 저장 성공: {values}")
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
                            print("CRC 오류 발생")
                    else:
                        buffer = buffer[1:] # 알 수 없는 기능코드 버림
            time.sleep(0.01)
        except Exception as e:
            print(f"수신 루프 에러: {e}")
            break

# ==========================================
# 4. 시간당 평균 계산 로직
# ==========================================
def calculate_hourly_avg():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.now()
    last_hour = (now - timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    start_str = last_hour.strftime('%Y-%m-%d %H:00:00')
    end_str = last_hour.strftime('%Y-%m-%d %H:59:59')

    col_names = ", ".join([f"D{900+i}" for i in range(NUM_WORDS)])
    avg_select = ", ".join([f"AVG(D{900+i})" for i in range(NUM_WORDS)])
    
    c.execute(f"SELECT {avg_select} FROM raw_data WHERE timestamp BETWEEN ? AND ?", (start_str, end_str))
    result = c.fetchone()

    if result and result[0] is not None:
        placeholders = ", ".join(["?"] * NUM_WORDS)
        c.execute(f"INSERT INTO hourly_avg (timestamp, {col_names}) VALUES (?, {placeholders})", [start_str] + list(result))
        conn.commit()
        print(f"[{start_str}] 시간당 평균 저장 완료")
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
        
        # Raw Data 최신 50개
        c.execute("SELECT * FROM raw_data WHERE timestamp LIKE ? ORDER BY timestamp DESC LIMIT 50", (f"{date_str}%",))
        self.display_table(self.raw_table, c.fetchall())

        # Average Data
        c.execute("SELECT * FROM hourly_avg WHERE timestamp LIKE ? ORDER BY timestamp DESC", (f"{date_str}%",))
        self.display_table(self.avg_table, c.fetchall())
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