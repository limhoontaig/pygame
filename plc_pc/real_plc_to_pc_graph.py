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

# Matplotlib 한글 폰트 설정 (Windows 기준 '맑은 고딕' 적용)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. 통신 및 데이터 설정 (PLC D900~D947 대응)
# ==========================================
COM_PORT = 'COM3'         # 실제 연결된 포트번호 확인
BAUD_RATE = 19200         # PLC 설정과 동일하게
MY_SLAVE_ID = 5           # PLC P2P 설정의 대상 국번
NUM_WORDS = 48            # D900 ~ D947 (총 48개 워드)
DB_NAME = "plc_logging_real.db"

# 48개 데이터 필드 레이블 정의 (날짜, 시간 제외)
DATA_LABELS = [
    "실내온도", "외기온도", "SF운전시간", "EF운전시간",
    "KEP_A_R", "KEP_A_S", "KEP_A_T", 
    "KEP_V_R", "KEP_V_S", "KEP_V_T", "KEP_V_R_S", "KEP_V_S_T", "KEP_V_T_R", 
    "KEP_P_kW", "KEP_P_mWh", 
    "Tr1_A_R", "Tr1_A_S", "Tr1_A_T", "Tr1_V_R", "Tr1_V_S", "Tr1_V_T", "Tr1_V_R_S", "Tr1_V_S_T", "Tr1_V_T_R", "Tr1_P_kW", "Tr1_Temp",
    "Tr2_A_R", "Tr2_A_S", "Tr2_A_T", "Tr2_V_R", "Tr2_V_S", "Tr2_V_T", "Tr2_V_R_S", "Tr2_V_S_T", "Tr2_V_T_R", "Tr2_P_kW", "Tr2_Temp",
    "Tr3_A_R", "Tr3_A_S", "Tr3_A_T", "Tr3_V_R", "Tr3_V_S", "Tr3_V_T", "Tr3_V_R_S", "Tr3_V_S_T", "Tr3_V_T_R", "Tr3_P_kW", "Tr3_Temp"
]

# 화면 출력용 전체 컬럼 헤더 라벨
COLUMN_LABELS = ["날짜", "시간"] + DATA_LABELS

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
    """데이터베이스 및 테이블 초기화 (데이터 레이블명으로 직접 컬럼 생성)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 실제 명칭 기반의 데이터 컬럼 구문 생성 (예: 실내온도 REAL, KEP_A_R REAL, ...)
    cols = ", ".join([f'"{name}" REAL' for name in DATA_LABELS])
    
    # 1. 원데이터 테이블 생성
    c.execute(f'CREATE TABLE IF NOT EXISTS raw_data (log_date DATE, log_time TIME, {cols})')
    
    # 2. 평균 데이터 테이블 생성
    c.execute(f'CREATE TABLE IF NOT EXISTS hourly_avg (log_date DATE, log_time TIME, {cols})')
    
    conn.commit()
    conn.close()

def insert_raw_data(values):
    """실시간 수신 데이터 스케일링 가공 및 저장"""
    if len(values) < NUM_WORDS:
        return
        
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        now = datetime.now()
        l_date = now.strftime('%Y-%m-%d')
        l_time = now.strftime('%H:%M:%S')
        
        adjusted_values = []
        for i, v in enumerate(values):
            # 10으로 나누는 항목 필터링 (D900~D906, Tr1_Temp, Tr2_Temp, Tr3_Temp)
            if i in [0, 1, 2, 3, 4, 5, 6]:  # 실내온도, 외기온도, SF운전시간, EF운전시간, KEP_A_R, KEP_A_S, KEP_A_T
                adjusted_values.append(v / 10.0)
            elif i in [25, 36, 47]:         # Tr1_Temp(D925), Tr2_Temp(D936), Tr3_Temp(D947)
                adjusted_values.append(v / 10.0)
                
            # 100으로 나누는 항목 필터링 (D907~D912, D914)
            elif i in [7, 8, 9, 10, 11, 12]: # KEP_V 계열 전압 필드들
                adjusted_values.append(v / 100.0)
            elif i == 14:                   # KEP_P_mWh(D914)
                adjusted_values.append(v / 100.0)
                
            # 나머지는 정수 형태 그대로 유지하여 저장
            else:
                adjusted_values.append(float(v))

        # DB 쿼리 생성 및 실행
        placeholders = ", ".join(["?"] * len(adjusted_values))
        col_names = ", ".join([f'"{name}"' for name in DATA_LABELS])
        
        query = f"INSERT INTO raw_data (log_date, log_time, {col_names}) VALUES (?, ?, {placeholders})"
        c.execute(query, [l_date, l_time] + adjusted_values)
        
        conn.commit()
        conn.close()
        print(f"[{l_date} {l_time}] DB 저장 성공 (48개 데이터 필드)")
    except Exception as e:
        print(f"DB 저장 오류: {e}")

# ==========================================
# 3. 시리얼 수신 엔진 (48 Words / 총 105바이트 대응)
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
                
                # 프레임 동기화: Slave ID(5)를 검색
                while len(buffer) >= 8:
                    if buffer[0] != MY_SLAVE_ID:
                        buffer = buffer[1:]
                        continue
                    
                    func_code = buffer[1]
                    if func_code == 0x10:
                        # PLC 송신 구조: [5][10][Addr2][Cnt2][Byte1][Data96][CRC2] = 총 105바이트
                        expected_len = 105 
                        if len(buffer) < expected_len: break # 데이터가 다 채워질 때까지 대기
                        
                        packet = buffer[:expected_len]
                        buffer = buffer[expected_len:]
                        
                        if verify_crc(packet):
                            # 데이터 파싱 위치 (국번~바이트수까지 7바이트 이후부터 데이터 블록 시작)
                            raw_values = packet[7:103] 
                            values = struct.unpack(f'>48h', raw_values) # Big Endian 48개 정수 언팩
                            insert_raw_data(values)
                        else:
                            hex_data = ' '.join([f'{b:02X}' for b in packet])
                            with open("comm_error_log.txt", "a") as f:
                                f.write(f"[{datetime.now()}] CRC Error: {hex_data}\n")
                            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CRC 오류 발생! 로그 저장됨.")
                    else:
                        buffer = buffer[1:] # 알 수 없는 기능코드는 버림
            time.sleep(0.01)
        except Exception as e:
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), f"수신 루프 에러: {e}")
            break

# ==========================================
# 4. 시간당 평균 계산 로직
# ==========================================
def calculate_hourly_avg():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=30)
        conn.execute("PRAGMA journal_mode = WAL") 
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
            placeholders = ", ".join(["?"] * NUM_WORDS)

            insert_query = f"INSERT INTO hourly_avg (log_date, log_time, {col_names}) VALUES (?, ?, {placeholders})"
            c.execute(insert_query, [target_date, f"{target_hour}:00:00"] + rounded_result)
            conn.commit()
            print(f"[{target_date} {target_hour}시] 시간당 평균 데이터 생성 완료.")
    except sqlite3.OperationalError as e:
        print(f"DB 잠김 오류 발생 (평균 계산): {e}")
    finally:
        conn.close()

# ==========================================
# 5. GUI 메인 윈도우 클래스 (PyQt5)
# ==========================================
class SCADAWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(10000) # 10초 주기 리프레시
        self.last_hour = datetime.now().hour

    def initUI(self):
        self.setWindowTitle("변전실 데이터 통합 모니터링 시스템 (48개 필드)")
        self.resize(1300, 850)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 상단 공통 제어 바
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

        # 화면 전환용 스택 위젯
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # --- 페이지 1: 데이터 테이블 화면 ---
        self.page_table = QWidget()
        table_layout = QVBoxLayout(self.page_table)
        splitter = QSplitter(Qt.Vertical)
        
        self.raw_table = QTableWidget()
        self.raw_table.setColumnCount(len(COLUMN_LABELS))
        self.raw_table.setHorizontalHeaderLabels(COLUMN_LABELS)
        
        self.avg_table = QTableWidget()
        self.avg_table.setColumnCount(len(COLUMN_LABELS))
        self.avg_table.setHorizontalHeaderLabels(COLUMN_LABELS)

        splitter.addWidget(QLabel("● 실시간 로그 (최근 50개 항목 표시)"))
        splitter.addWidget(self.raw_table)
        splitter.addWidget(QLabel("● 시간별 평균 데이터 추이"))
        splitter.addWidget(self.avg_table)
        table_layout.addWidget(splitter)
        self.stack.addWidget(self.page_table)

        # --- 페이지 2: 그래프 분석 화면 ---
        self.page_graph = QWidget()
        graph_layout = QVBoxLayout(self.page_graph)
        
        graph_ctrl = QHBoxLayout()
        self.data_selector = QComboBox()
        self.data_selector.addItems(DATA_LABELS) # 한글 데이터 레이블 직접 등록
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

        # 버튼 이벤트 시그널 연결
        self.btn_show_table.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_show_graph.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        # 필터값 변경 시 자동 업데이트
        self.qdate.dateChanged.connect(self.auto_refresh)
        self.data_selector.currentIndexChanged.connect(self.update_graph)
        self.period_selector.currentIndexChanged.connect(self.update_graph)

        self.load_data()

    def load_data(self):
        date_str = self.qdate.date().toString("yyyy-MM-dd")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            # Raw Data 조회
            c.execute("SELECT * FROM raw_data WHERE log_date = ? ORDER BY log_time DESC LIMIT 50", (date_str,))
            self.display_table(self.raw_table, c.fetchall())
            
            # Average Data 조회
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
        # 컬럼 이름에 특수문자나 한글이 들어가므로 따옴표 처리가 필수입니다.
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
            
            # X축 인덱스 눈금 최적화
            import matplotlib.ticker as ticker
            self.ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
            
            self.ax.set_title(f"[{target_col}] {period} 데이터 추이 분석")
            self.ax.grid(True, linestyle='--', alpha=0.7)
            self.canvas.figure.autofmt_xdate() 
        else:
            self.ax.text(0.5, 0.5, "해당 기간의 데이터가 존재하지 않습니다.", ha='center')
        
        self.canvas.draw()

    def display_table(self, table, rows):
        table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                txt = f"{val:.1f}" if isinstance(val, float) else str(val)
                table.setItem(r_idx, c_idx, QTableWidgetItem(txt))

    def auto_refresh(self):
        curr_hour = datetime.now().hour
        if curr_hour != self.last_hour:
            calculate_hourly_avg()
            self.last_hour = curr_hour
        self.load_data()
        self.update_graph()

# ==========================================
# 6. 프로그램 메인 실행부
# ==========================================
if __name__ == "__main__":
    init_db()
    
    # 시리얼 패킷 상시 수신 스레드 기동
    t = threading.Thread(target=serial_receive_thread, daemon=True)
    t.start()
    
    app = QApplication(sys.argv)
    win = SCADAWindow()
    win.show()
    sys.exit(app.exec_())