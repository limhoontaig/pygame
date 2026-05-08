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
                            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " CRC 오류 발생")
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
    conn = sqlite3.connect(DB_NAME)
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
        
        conn.close())

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