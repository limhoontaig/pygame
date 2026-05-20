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
COLUMN_LABELS = ["날짜", "시간/구분"] + DATA_LABELS

# ==========================================
# 2. 데이터베이스 초기화 및 저장 로직
# ==========================================
def init_db():
    """데이터베이스 및 테이블 초기화"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 실제 명칭 기반의 데이터 컬럼 구문 생성
    cols = ", ".join([f'"{name}" REAL' for name in DATA_LABELS])
    
    # 1. 원데이터 테이블 생성
    c.execute(f'CREATE TABLE IF NOT EXISTS raw_data (log_date DATE, log_time TIME, {cols})')
    
    # 2. 평균 데이터 테이블 생성
    c.execute(f'CREATE TABLE IF NOT EXISTS hourly_avg (log_date DATE, log_time TIME, {cols})')
    
    # 3. [추가] 일일 최고/최저 통계 테이블 생성
    c.execute(f'''CREATE TABLE IF NOT EXISTS daily_extremes (
                    log_date DATE, 
                    extreme_type TEXT, 
                    {cols},
                    PRIMARY KEY (log_date, extreme_type)
                  )''')
    
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
            # 10으로 나누는 항목 필터링
            if i in [0, 1, 2, 3, 4, 5, 6]:
                adjusted_values.append(v / 10.0)
            elif i in [25, 36, 47]:
                adjusted_values.append(v / 10.0)
            # 100으로 나누는 항목 필터링
            elif i in [7, 8, 9, 10, 11, 12]:
                adjusted_values.append(v / 100.0)
            elif i == 14:
                adjusted_values.append(v / 100.0)
            # 정수 유지
            else:
                adjusted_values.append(float(v))

        placeholders = ", ".join(["?"] * len(adjusted_values))
        col_names = ", ".join([f'"{name}"' for name in DATA_LABELS])
        
        query = f"INSERT INTO raw_data (log_date, log_time, {col_names}) VALUES (?, ?, {placeholders})"
        c.execute(query, [l_date, l_time] + adjusted_values)
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB 저장 오류: {e}")

# ==========================================
# 3. [추가 및 수정] 통계 계산 로직 (평균 및 최고/최저)
# ==========================================
def calculate_hourly_avg():
    """시간당 평균 계산"""
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
            placeholders = ", ".join(["?"] * NUM_WORDS)

            insert_query = f"INSERT INTO hourly_avg (log_date, log_time, {col_names}) VALUES (?, ?, {placeholders})"
            c.execute(insert_query, [target_date, f"{target_hour}:00:00"] + rounded_result)
            conn.commit()
            print(f"[{target_date} {target_hour}시] 시간당 평균 데이터 생성 완료.")
    except Exception as e:
        print(f"평균 계산 오류: {e}")
    finally:
        conn.close()

def calculate_daily_extremes(target_date):
    """지정된 날짜의 데이터 전체를 분석하여 최고값(MAX)과 최저값(MIN)을 갱신 저장합니다."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=30)
        c = conn.cursor()
        
        # 48개 컬럼에 대해 각각 MAX와 MIN을 구하는 쿼리 생성
        max_select = ", ".join([f'MAX("{name}")' for name in DATA_LABELS])
        min_select = ", ".join([f'MIN("{name}")' for name in DATA_LABELS])
        col_names = ", ".join([f'"{name}"' for name in DATA_LABELS])
        placeholders = ", ".join(["?"] * NUM_WORDS)
        
        # 1. 최고값(MAX) 계산 및 저장 (REPLACE 구문으로 기존 통계 덮어쓰기)
        c.execute(f'SELECT {max_select} FROM raw_data WHERE log_date = ?', (target_date,))
        max_res = c.fetchone()
        if max_res and max_res[0] is not None:
            c.execute(f'INSERT OR REPLACE INTO daily_extremes (log_date, extreme_type, {col_names}) VALUES (?, ?, {placeholders})',
                      [target_date, 'MAX'] + list(max_res))
            
        # 2. 최저값(MIN) 계산 및 저장
        c.execute(f'SELECT {min_select} FROM raw_data WHERE log_date = ?', (target_date,))
        min_res = c.fetchone()
        if min_res and min_res[0] is not None:
            c.execute(f'INSERT OR REPLACE INTO daily_extremes (log_date, extreme_type, {col_names}) VALUES (?, ?, {placeholders})',
                      [target_date, 'MIN'] + list(min_res))
            
        conn.commit()
        print(f"[{target_date}] 일일 최고/최저값 데이터 동기화 완료.")
    except Exception as e:
        print(f"최고/최저 통계 계산 오류: {e}")
    finally:
        conn.close()

# ==========================================
# 4. 시리얼 수신 엔진
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
                while len(buffer) >= 8:
                    if buffer[0] != MY_SLAVE_ID:
                        buffer = buffer[1:]
                        continue
                    
                    func_code = buffer[1]
                    if func_code == 0x10:
                        expected_len = 105 
                        if len(buffer) < expected_len: break
                        
                        packet = buffer[:expected_len]
                        buffer = buffer[expected_len:]
                        
                        # 간단 검증 또는 내장 CRC 통과 시
                        raw_values = packet[7:103] 
                        values = struct.unpack(f'>48h', raw_values)
                        insert_raw_data(values)
                    else:
                        buffer = buffer[1:]
            time.sleep(0.01)
        except Exception as e:
            print(f"수신 루프 에러: {e}")
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
        self.timer.start(10000) # 10초 주기 리프레시
        self.last_hour = datetime.now().hour

    def initUI(self):
        self.setWindowTitle("변전실 데이터 통합 모니터링 시스템 (최고/최저 통계 포함)")
        self.resize(1400, 900)
        
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
        
        # 1. 실시간 로그 테이블
        self.raw_table = QTableWidget()
        self.raw_table.setColumnCount(len(COLUMN_LABELS))
        self.raw_table.setHorizontalHeaderLabels(COLUMN_LABELS)
        
        # 2. 시간별 평균 테이블
        self.avg_table = QTableWidget()
        self.avg_table.setColumnCount(len(COLUMN_LABELS))
        self.avg_table.setHorizontalHeaderLabels(COLUMN_LABELS)

        # 3. [추가] 일일 최고/최저 요약 테이블
        self.extreme_table = QTableWidget()
        self.extreme_table.setColumnCount(len(COLUMN_LABELS))
        self.extreme_table.setHorizontalHeaderLabels(COLUMN_LABELS)

        splitter.addWidget(QLabel("● 실시간 로그 (최근 50개 항목 표시)"))
        splitter.addWidget(self.raw_table)
        splitter.addWidget(QLabel("● 시간별 평균 데이터 추이"))
        splitter.addWidget(self.avg_table)
        splitter.addWidget(QLabel("● 일일 최고(MAX) / 최저(MIN) 값 요약 정보")) # 추가된 레이블
        splitter.addWidget(self.extreme_table)                                    # 추가된 테이블
        
        table_layout.addWidget(splitter)
        self.stack.addWidget(self.page_table)

        # --- 페이지 2: 그래프 분석 화면 ---
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

        # 버튼 및 시그널 바인딩
        self.btn_show_table.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_show_graph.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        self.qdate.dateChanged.connect(self.auto_refresh)
        self.data_selector.currentIndexChanged.connect(self.update_graph)
        self.period_selector.currentIndexChanged.connect(self.update_graph)

        self.load_data()

    def load_data(self):
        date_str = self.qdate.date().toString("yyyy-MM-dd")
        
        # 데이터 로드 전 선택된 날짜의 최고/최저값 한 번 실시간 갱신 연산 수행
        calculate_daily_extremes(date_str)
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            # 1. Raw Data 조회
            c.execute("SELECT * FROM raw_data WHERE log_date = ? ORDER BY log_time DESC LIMIT 50", (date_str,))
            self.display_table(self.raw_table, c.fetchall())
            
            # 2. Average Data 조회
            c.execute("SELECT * FROM hourly_avg WHERE log_date = ? ORDER BY log_time DESC", (date_str,))
            self.display_table(self.avg_table, c.fetchall())
            
            # 3. [추가] 최고/최저 통계 조회 (MAX가 먼저 보이게 정렬)
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
                
                # [시각 효과 추가] 최고값은 연한 빨간색, 최저값은 연한 파란색 배경 지정
                if is_extreme:
                    if row[1] == 'MAX':
                        item.setBackground(Qt.cyan if c_idx == 1 else Qt.transparent) # 구분을 돋보이게 하거나
                        # 최고값 행 전체에 부드러운 빨간색 틴트 적용
                        if c_idx > 1: item.setForeground(Qt.red)
                    elif row[1] == 'MIN':
                        if c_idx > 1: item.setForeground(Qt.blue)
                        
                table.setItem(r_idx, c_idx, item)

    def auto_refresh(self):
        curr_hour = datetime.now().hour
        date_str = self.qdate.date().toString("yyyy-MM-dd")
        
        # 정시가 변경되면 시간당 평균 계산 수행
        if curr_hour != self.last_hour:
            calculate_hourly_avg()
            self.last_hour = curr_hour
            
        # 데이터를 불러올 때 최고/최저 자동 연산 동시 실행
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