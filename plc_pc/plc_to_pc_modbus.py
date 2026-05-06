#cd c:\pygame\plc_pc; pyinstaller --onefile --windowed --name "PLC_Modbus_RTU" plc_to_pc_modbus.py

import sys
import serial
import threading
import sqlite3
import struct
import time
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, QLabel, QHBoxLayout,
                             QDateEdit, QTimeEdit, QComboBox, QGridLayout, QGroupBox, QSplitter)
from PyQt5.QtCore import QTimer, QDate, QTime, Qt

# ==========================================
# Modbus RTU RS-485 통신 설정
# ==========================================
# [통신 구조]
# PLC (마스터) → RS-485 → PC (슬레이브)
# - PLC가 주기적으로 데이터를 PC로 전송
# - PC는 스레이브 번호 5번으로 설정되어 수신 대기
# - 수신된 데이터는 SQLite DB에 저장
# ==========================================

COM_PORT = 'COM6'      # 장치 관리자에서 확인한 포트 번호로 변경하세요
BAUD_RATE = 19200       # PLC의 통신 속도 설정과 반드시 일치해야 합니다 (예: 9600, 19200, 38400)
PARITY = serial.PARITY_NONE  # 패리티: None, Even, Odd
STOP_BITS = 1          # 스톱 비트: 1 또는 2
BYTE_SIZE = 8          # 데이터 비트: 8

NUM_WORDS = 14         # D100 ~ D113 (14개)
DB_NAME = "plc_data.db"

# ==========================================
# PC 슬레이브 설정 (PLC가 데이터를 보내는 대상)
# ==========================================
# PLC에서 이 번호로 데이터를 보내면 PC가 수신합니다.
# PLC 프로그램에서 스레이브 5번으로 설정하세요.
MY_SLAVE_ID = 5

# ==========================================
# Modbus RTU CRC16 계산 함수
# ==========================================
def calculate_crc(data):
    """Modbus RTU CRC-16 (CRC-16/MODBUS) 계산"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    # LSB first (little-endian)
    return struct.pack('<H', crc)

def verify_crc(data):
    """수신 데이터의 CRC 검증 (바이트 순서 교차 대응)"""
    if len(data) < 4:
        return False
    
    # 1. 데이터 본문과 수신된 CRC 분리
    body = data[:-2]
    received_crc = data[-2:] # 28 07 형태
    
    # 2. 직접 계산한 CRC (표준 방식)
    calc_crc_bytes = calculate_crc(body) # 결과가 07 28 형태라고 가정
    
    # 3. 표준 방식(received_crc) 또는 바이트가 반전된 방식 모두 체크
    if received_crc == calc_crc_bytes:
        return True
    
    # 만약 반전되어 들어온다면 (28 07 <-> 07 28)
    if received_crc == calc_crc_bytes[::-1]:
        return True
        
    return False

# ==========================================
# Modbus RTU 기능 코드 정의
# ==========================================
FUNC_READ_COILS = 0x01           # 읽기: 코일
FUNC_READ_DISCRETE = 0x02        # 읽기: 디스크리트 입력
FUNC_READ_HOLDING = 0x03         # 읽기: 홀딩 레지스터
FUNC_READ_INPUT = 0x04           # 읽기: 입력 레지스터
FUNC_WRITE_SINGLE = 0x06         # 쓰기: 단일 레지스터
FUNC_WRITE_MULTI = 0x10           # 쓰기: 다중 레지스터
FUNC_READ_WRITE = 0x17            # 읽기/쓰기 다중 레지스터

# ==========================================
# 컬럼 라벨 정의 (D100 ~ D113)
# ==========================================
# D100-D101: 실내온도, 외기온도 (2개)
# D102-D119: 변압기1-5 (전압, 전류, 전력, 온도 × 5대 = 18개)
COLUMN_LABELS = ["시간", "실내온도", "외기온도", "변압기1전압", "변압기1전류", "변압기1전력", "변압기1온도",
                 "변압기2전압", "변압기2전류", "변압기2전력", "변압기2온도",
                 "변압기3전압", "변압기3전류", "변압기3전력", "변압기3온도"]

#=========================================
# TCP/IP 설정 (PLC가 Master로 데이터를 전송하는 경우)
# PLC에서 PC로 데이터를 전송할 때 사용할 IP와 포트 번호를 설정합니다.
# PLC가 Master로 데이터를 전송하는 경우, PC는 TCP 서버 역할을 하며, PLC는 TCP 클라이언트로 동작합니다.
#
# TCP_IP = "0.0.0.0"  # 모든 IP에서 수신 대기 (PC의 IP)
# TCP_PORT = 5020     # PLC에서 데이터를 전송할 포트 번호
# NUM_WORDS = 14      # D100 ~ D113 (14개)
#=========================================

# ==========================================
# 1. 데이터베이스 관리 (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # D100 ~ D113 컬럼 생성 문자열 (d100 INTEGER, d101 INTEGER ...)
    columns = ", ".join([f"{COLUMN_LABELS[i]} INTEGER" for i in range(NUM_WORDS)])
    
    # 원데이터 테이블 생성 (1분 주기)
    c.execute(f"CREATE TABLE IF NOT EXISTS raw_data (timestamp DATETIME, {columns})")
    # 1시간 평균 데이터 테이블 생성
    c.execute(f"CREATE TABLE IF NOT EXISTS hourly_avg (timestamp DATETIME, {columns})")
    
    conn.commit()
    conn.close()

def insert_raw_data(values):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    placeholders = ", ".join(["?"] * NUM_WORDS)
    c.execute(f"INSERT INTO raw_data (timestamp, {', '.join([f'{COLUMN_LABELS[i]}' for i in range(NUM_WORDS)])}) VALUES (?, {placeholders})", [now] + list(values))
    
    conn.commit()
    conn.close()
    print(f"[{now}] 원데이터 저장 완료: {values}")

def calculate_hourly_avg():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1시간 전 시간 계산
    now = datetime.now()
    last_hour_start = (now - timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    last_hour_end = last_hour_start.replace(minute=59, second=59)
    
    # 해당 시간대의 평균값 계산 쿼리
    avg_columns = ", ".join([f"AVG({COLUMN_LABELS[i]})" for i in range(NUM_WORDS)])
    query = f"SELECT {avg_columns} FROM raw_data WHERE timestamp BETWEEN ? AND ?"
    
    c.execute(query, (last_hour_start.strftime('%Y-%m-%d %H:%M:%S'), last_hour_end.strftime('%Y-%m-%d %H:%M:%S')))
    result = c.fetchone()
    
    # 데이터가 존재하고 첫번째 값이 None이 아닐 때만 저장
    if result and result[0] is not None:
        target_time = last_hour_start.strftime('%Y-%m-%d %H:00:00')
        placeholders = ", ".join(["?"] * NUM_WORDS)
        insert_query = f"INSERT INTO hourly_avg (timestamp, {', '.join([f'{COLUMN_LABELS[i]}' for i in range(NUM_WORDS)])}) VALUES (?, {placeholders})"
        c.execute(insert_query, [target_time] + list(result))
        conn.commit()
        print(f"[{target_time}] 1시간 평균 데이터 산출 및 저장 완료")
        
    conn.close()


# ==========================================
# 2. Modbus RTU 스레이브 수신 (PLC → PC)
# ==========================================
# [동작 설명]
# - PLC (마스터)가 주기적으로 데이터를 전송
# - PC (슬레이브)는 스레이브 번호 5번으로 수신 대기
# - 수신된 데이터: [스레이브5][기능코드0x03][데이터40바이트][CRC2]
# - 데이터는 SQLite DB에 저장
# ==========================================
def serial_receive_thread():
    try:
        ser = serial.Serial(
            port=COM_PORT,
            baudrate=BAUD_RATE,
            bytesize=BYTE_SIZE,
            parity=PARITY,
            stopbits=STOP_BITS,
            timeout=0.05  # 짧은 타임아웃으로 패킷 분리 유도
        )
        print(f"Modbus RTU 포트 열림: {COM_PORT} ({BAUD_RATE}bps, 8N1)")
    except Exception as e:
        print(f"시리얼 포트 연결 실패: {e}")
        return

    buffer = b""  # 수신 잔여 데이터를 저장할 버퍼

    while True:
        try:
            if ser.in_waiting > 0:
                # 1. 일단 읽을 수 있는 만큼 읽어 버퍼에 추가
                buffer += ser.read(ser.in_waiting)
                
                # 2. 버퍼에 데이터가 있고, 최소 프레임 길이(Slave+Func+Len+Data+CRC = 최소 5~8바이트) 이상일 때 루프
                while len(buffer) >= 5:
                    # 2-1. 내 슬레이브 번호(5)가 나올 때까지 앞부분 버림 (동기화)
                    if buffer[0] != MY_SLAVE_ID:
                        buffer = buffer[1:]
                        continue
                    
                    # 2-2. 기능 코드 확인 (0x03: Read Holding, 0x10: Write Multi 등)
                    func_code = buffer[1]
                    
                    # 수신 패킷 길이를 예측 (기능 코드에 따라 다름)
                    if func_code == 0x03:
                        if len(buffer) < 3: break # 데이터 길이 바이트 대기
                        expected_len = buffer[2] + 5 # [ID][Func][Len] + [Data] + [CRC2]
                    elif func_code == 0x10:
                        expected_len = 8 # Write Multi 응답은 항상 8바이트
                    elif func_code == 0x06:
                        expected_len = 8 # Write Single 응답은 항상 8바이트
                    else:
                        # 알 수 없는 기능코드면 1바이트 버리고 다시 찾기
                        buffer = buffer[1:]
                        continue

                    # 2-3. 전체 패킷이 아직 다 안 들어왔으면 다음 읽기 대기
                    if len(buffer) < expected_len:
                        break
                    
                    # 2-4. 완성된 패킷 추출 및 검증
                    packet = buffer[:expected_len]
                    buffer = buffer[expected_len:] # 버퍼에서 패킷 제거
                    
                    if verify_crc(packet):
                        # 정상 패킷 처리
                        if func_code == FUNC_READ_HOLDING:
                            byte_count = packet[2]
                            raw_data = packet[3:3+byte_count]
                            # 데이터 파싱 (리틀 엔디안 방식 주의: PLC 설정 확인 필요)
                            # PLC가 대중적으로 사용하는 Big Endian이면 '>h' 사용
                            values = struct.unpack(f'>{byte_count//2}h', raw_data)
                            insert_raw_data(values)
                            print(f"데이터 수신 성공: {values}")
                    else:
                        print(f"CRC 오류 패킷 폐기: {packet.hex()}")

            time.sleep(0.01) # CPU 부하 방지
            
        except Exception as e:
            print(f"통신 에러 발생: {e}")
            time.sleep(1) # 에러 시 잠시 대기 후 재시도
    ser.close()


# ==========================================
# 3. Modbus RTU 마스터 기능 (PC → PLC 쓰기)
# ==========================================
class ModbusMaster:
    """Modbus RTU 마스터 (PLC에 데이터 쓰기)"""
    
    def __init__(self, port=COM_PORT, baudrate=BAUD_RATE):
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=BYTE_SIZE,
            parity=PARITY,
            stopbits=STOP_BITS,
            timeout=1.0
        )
    
    def write_single_register(self, slave_id, register_addr, value):
        """단일 레지스터 쓰기 (기능코드 0x06)"""
        # 프레임: [슬레이브][기능코드][레지스터H][레지스터L][값H][값L][CRC]
        frame = struct.pack('>BBHHH', 
                           slave_id,           # 스레이브 번호
                           FUNC_WRITE_SINGLE,  # 기능코드 0x06
                           register_addr,      # 레지스터 주소 (D100 = 100)
                           value,              # 쓸 값
                           0)                  # 더미 (CRC 계산 후 교체)
        
        # CRC 계산
        crc = calculate_crc(frame[:-2])  # 마지막 2바이트 제외
        frame = frame[:-2] + crc
        
        # 전송
        self.ser.write(frame)
        
        # 응답 수신
        response = self.ser.read(8)
        if len(response) >= 5 and verify_crc(response):
            print(f"D{register_addr} ← {value} (스레이브 {slave_id})")
            return True
        return False
    
    def write_multiple_registers(self, slave_id, start_addr, values):
        """다중 레지스터 쓰기 (기능코드 0x10)"""
        register_count = len(values)
        byte_count = register_count * 2
        
        # PDU 구성
        pdu = struct.pack('>BBHHB', 
                         slave_id,
                         FUNC_WRITE_MULTI,  # 0x10
                         start_addr,
                         register_count,
                         byte_count)
        
        # 데이터 추가
        data_bytes = struct.pack(f'<{register_count}h', *values)
        frame = pdu + data_bytes
        
        # CRC 계산
        crc = calculate_crc(frame)
        frame = frame + crc
        
        # 전송
        self.ser.write(frame)
        
        # 응답 수신 (최소 8바이트)
        response = self.ser.read(8)
        if len(response) >= 8 and verify_crc(response):
            print(f"D{start_addr}부터 {register_count}개 쓰기 완료 (스레이브 {slave_id})")
            return True
        return False
    
    def read_holding_registers(self, slave_id, start_addr, count):
        """홀딩 레지스터 읽기 (기능코드 0x03)"""
        # 프레임: [슬레이브][기능코드][시작주소H][시작주소L][개수H][개수L][CRC]
        frame = struct.pack('>BBHHH', 
                           slave_id,
                           FUNC_READ_HOLDING,  # 0x03
                           start_addr,
                           count,
                           0)
        
        crc = calculate_crc(frame[:-2])
        frame = frame[:-2] + crc
        
        self.ser.write(frame)
        
        # 응답: [슬레이브][기능코드][바이트수][데이터...][CRC]
        response = self.ser.read(5 + count * 2)
        
        if len(response) >= 5 and verify_crc(response):
            byte_count = response[2]
            data = response[3:3+byte_count]
            return struct.unpack(f'<{byte_count//2}h', data)
        return None
    
    def close(self):
        self.ser.close()


# ==========================================
# 4. GUI 화면 구성 (PyQt5)
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("미니 SCADA - 1시간 평균 데이터 조회")
        self.resize(1000, 600)
        
        # 메인 위젯 및 레이아웃
        main_widget = QWidget()
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        
        # ==========================================
        # 상단: 날짜/시간 선택 영역
        # ==========================================
        search_group = QGroupBox("데이터 검색")
        search_layout = QGridLayout()
        
        # 시작 날짜
        search_layout.addWidget(QLabel("시작 날짜:"), 0, 0)
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        search_layout.addWidget(self.start_date, 0, 1)
        
        # 시작 시간
        search_layout.addWidget(QLabel("시작 시간:"), 0, 2)
        self.start_time = QTimeEdit()
        self.start_time.setTime(QTime(0, 0, 0))
        search_layout.addWidget(self.start_time, 0, 3)
        
        # 종료 날짜
        search_layout.addWidget(QLabel("종료 날짜:"), 1, 0)
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        search_layout.addWidget(self.end_date, 1, 1)
        
        # 종료 시간
        search_layout.addWidget(QLabel("종료 시간:"), 1, 2)
        self.end_time = QTimeEdit()
        self.end_time.setTime(QTime(23, 59, 59))
        search_layout.addWidget(self.end_time, 1, 3)
        
        # 검색 버튼
        self.search_btn = QPushButton("검색")
        self.search_btn.clicked.connect(self.search_data)
        search_layout.addWidget(self.search_btn, 0, 4, 1, 2)
        
        # 새로고침 버튼
        self.refresh_btn = QPushButton("전체 데이터 새로고침")
        self.refresh_btn.clicked.connect(self.load_data)
        search_layout.addWidget(self.refresh_btn, 1, 4, 1, 2)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # ==========================================
        # 하단: 좌우 분할 화면 (원데이터 + 평균데이터)
        # ==========================================
        splitter = QSplitter(Qt.Horizontal)
        
        # ----- 왼쪽: 원데이터 테이블 -----
        raw_group = QGroupBox("1분 원데이터 (raw_data)")
        raw_layout = QVBoxLayout()
        self.raw_label = QLabel("원데이터: 0개")
        raw_layout.addWidget(self.raw_label)
        self.raw_table = QTableWidget()
        self.raw_table.setColumnCount(NUM_WORDS + 1)
        self.raw_table.setHorizontalHeaderLabels(COLUMN_LABELS)
        raw_layout.addWidget(self.raw_table)
        raw_group.setLayout(raw_layout)
        splitter.addWidget(raw_group)
        
        # ----- 오른쪽: 평균데이터 테이블 -----
        avg_group = QGroupBox("1시간 평균 (hourly_avg)")
        avg_layout = QVBoxLayout()
        self.avg_label = QLabel("평균데이터: 0개")
        avg_layout.addWidget(self.avg_label)
        self.avg_table = QTableWidget()
        self.avg_table.setColumnCount(NUM_WORDS + 1)
        self.avg_table.setHorizontalHeaderLabels(COLUMN_LABELS)
        avg_layout.addWidget(self.avg_table)
        avg_group.setLayout(avg_layout)
        splitter.addWidget(avg_group)
        
        layout.addWidget(splitter)
        
        # 정보 라벨
        self.info_label = QLabel("데이터를 선택하세요.")
        layout.addWidget(self.info_label)
        
        # 주기적 작업 설정 (스케줄러 역할)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_and_calculate_avg)
        self.timer.start(60000) # 1분마다 체크
        self.last_calc_hour = datetime.now().hour
        
        # 초기 데이터 로드
        self.load_data()

    def search_data(self):
        """날짜/시간 범위로 데이터 검색 (두 테이블에 동시 표시)"""
        # 시작 날짜/시간
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        start_time = self.start_time.time().toString("HH:mm:ss")
        start_datetime = f"{start_date} {start_time}"
        
        # 종료 날짜/시간
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        end_time = self.end_time.time().toString("HH:mm:ss")
        end_datetime = f"{end_date} {end_time}"
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # ----- 원데이터 조회 -----
        c.execute("SELECT * FROM raw_data WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp DESC LIMIT 500", 
                  (start_datetime, end_datetime))
        raw_rows = c.fetchall()
        
        # ----- 평균데이터 조회 -----
        c.execute("SELECT * FROM hourly_avg WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp DESC LIMIT 500", 
                  (start_datetime, end_datetime))
        avg_rows = c.fetchall()
        
        conn.close()
        
        # ----- 원데이터 테이블 표시 -----
        self.raw_table.setRowCount(len(raw_rows))
        for row_idx, row_data in enumerate(raw_rows):
            for col_idx, value in enumerate(row_data):
                display_val = f"{value:.2f}" if isinstance(value, float) else str(value)
                self.raw_table.setItem(row_idx, col_idx, QTableWidgetItem(display_val))
        
        # ----- 평균데이터 테이블 표시 -----
        self.avg_table.setRowCount(len(avg_rows))
        for row_idx, row_data in enumerate(avg_rows):
            for col_idx, value in enumerate(row_data):
                display_val = f"{value:.2f}" if isinstance(value, float) else str(value)
                self.avg_table.setItem(row_idx, col_idx, QTableWidgetItem(display_val))
        
        # ----- 라벨 업데이트 -----
        self.raw_label.setText(f"원데이터: {len(raw_rows)}개")
        self.avg_label.setText(f"평균데이터: {len(avg_rows)}개")
        self.info_label.setText(f"검색 결과 (기간: {start_datetime} ~ {end_datetime})")

    def load_data(self):
        """DB에서 전체 데이터를 읽어와 두 테이블에 표시"""
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # 원데이터 최신 100개
        c.execute("SELECT * FROM raw_data ORDER BY timestamp DESC LIMIT 100")
        raw_rows = c.fetchall()
        
        # 평균데이터 최신 100개
        c.execute("SELECT * FROM hourly_avg ORDER BY timestamp DESC LIMIT 100")
        avg_rows = c.fetchall()
        
        conn.close()
        
        # ----- 원데이터 테이블 표시 -----
        self.raw_table.setRowCount(len(raw_rows))
        for row_idx, row_data in enumerate(raw_rows):
            for col_idx, value in enumerate(row_data):
                display_val = f"{value:.2f}" if isinstance(value, float) else str(value)
                self.raw_table.setItem(row_idx, col_idx, QTableWidgetItem(display_val))
        
        # ----- 평균데이터 테이블 표시 -----
        self.avg_table.setRowCount(len(avg_rows))
        for row_idx, row_data in enumerate(avg_rows):
            for col_idx, value in enumerate(row_data):
                display_val = f"{value:.2f}" if isinstance(value, float) else str(value)
                self.avg_table.setItem(row_idx, col_idx, QTableWidgetItem(display_val))
        
        # ----- 라벨 업데이트 -----
        self.raw_label.setText(f"원데이터: {len(raw_rows)}개")
        self.avg_label.setText(f"평균데이터: {len(avg_rows)}개")
        self.info_label.setText("전체 데이터 (최신 100개씩)")

    def check_and_calculate_avg(self):
        """매시간 정각이 지났는지 확인하고 평균 계산 함수 호출"""
        current_hour = datetime.now().hour
        if current_hour != self.last_calc_hour:
            calculate_hourly_avg()
            self.last_calc_hour = current_hour
            self.load_data()  # 계산 후 화면 갱신 (두 테이블 동시)

if __name__ == "__main__":
    # 1. DB 초기화
    init_db()
    
    # 2. 통신 스레드 시작 (백그라운드에서 계속 실행)
    serial_thread = threading.Thread(target=serial_receive_thread, daemon=True)
    serial_thread.start()
    
    # 3. GUI 앱 실행
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())