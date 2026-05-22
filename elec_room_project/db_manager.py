import sqlite3
import struct
from datetime import datetime, timedelta

DB_NAME = "plc_logging_real.db"
DATA_LABELS = [
    "실내온도", "외기온도", "SF운전시간", "EF운전시간", "KEP_A_R", "KEP_A_S", "KEP_A_T", 
    "KEP_V_R", "KEP_V_S", "KEP_V_T", "KEP_V_R_S", "KEP_V_S_T", "KEP_V_T_R", 
    "KEP_frequency", "KEP_P_kW", "KEP_P_kWh", 
    "Tr1_A_R", "Tr1_A_S", "Tr1_A_T", "Tr1_V_R", "Tr1_V_S", "Tr1_V_T", "Tr1_V_R_S", "Tr1_V_S_T", "Tr1_V_T_R", "Tr1_P_kW", "Tr1_Temp",
    "Tr2_A_R", "Tr2_A_S", "Tr2_A_T", "Tr2_V_R", "Tr2_V_S", "Tr2_V_T", "Tr2_V_R_S", "Tr2_V_S_T", "Tr2_V_T_R", "Tr2_P_kW", "Tr2_Temp",
    "Tr3_A_R", "Tr3_A_S", "Tr3_A_T", "Tr3_V_R", "Tr3_V_S", "Tr3_V_T", "Tr3_V_R_S", "Tr3_V_S_T", "Tr3_V_T_R", "Tr3_P_kW", "Tr3_Temp"
]

COLUMN_LABELS = ["날짜", "시간/구분"] + DATA_LABELS

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    cols = ", ".join([f'"{name}" REAL' for name in DATA_LABELS])
    c.execute(f'CREATE TABLE IF NOT EXISTS raw_data (log_date DATE, log_time TIME, {cols})')
    c.execute(f'CREATE TABLE IF NOT EXISTS hourly_avg (log_date DATE, log_time TIME, {cols})')
    c.execute(f'CREATE TABLE IF NOT EXISTS daily_extremes (log_date DATE, extreme_type TEXT, {cols}, PRIMARY KEY (log_date, extreme_type))')
    conn.commit()
    conn.close()

def insert_raw_data(values):
    if len(values) < len(DATA_LABELS): return
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        now = datetime.now()
        l_date, l_time = now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S')
        
        DIV_BY_10 = {"실내온도", "외기온도", "SF운전시간", "EF운전시간", "Tr1_Temp", "Tr2_Temp", "Tr3_Temp"}
        DIV_BY_100 = {"KEP_A_R", "KEP_A_S", "KEP_A_T", "KEP_frequency", "KEP_V_R", "KEP_V_S", "KEP_V_T", "KEP_V_R_S", "KEP_V_S_T", "KEP_V_T_R", "KEP_P_mWh"}
        
        adjusted_values = []
        for label, val in zip(DATA_LABELS, values):
            if label in DIV_BY_10: adjusted_values.append(val / 10.0)
            elif label in DIV_BY_100: adjusted_values.append(val / 100.0)
            else: adjusted_values.append(float(val))

        placeholders = ", ".join(["?"] * len(adjusted_values))
        col_names = ", ".join([f'"{name}"' for name in DATA_LABELS])
        c.execute(f"INSERT INTO raw_data (log_date, log_time, {col_names}) VALUES (?, ?, {placeholders})", [l_date, l_time] + adjusted_values)
        conn.commit()
        conn.close()
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
            c.execute(f'INSERT OR REPLACE INTO daily_extremes (log_date, extreme_type, {col_names}) VALUES (?, ?, {placeholders})', [target_date, 'MAX'] + list(max_res))
            
        c.execute(f'SELECT {min_select} FROM raw_data WHERE log_date = ?', (target_date,))
        min_res = c.fetchone()
        if min_res and min_res[0] is not None:
            c.execute(f'INSERT OR REPLACE INTO daily_extremes (log_date, extreme_type, {col_names}) VALUES (?, ?, {placeholders})', [target_date, 'MIN'] + list(min_res))
        conn.commit()
    except Exception as e:
        print(f"최고/최저 계산 오류: {e}")
    finally:
        conn.close()

def verify_crc(data):
    if len(data) < 4: return False
    body = data[:-2]
    recv_crc = data[-2:]
    calc_crc = calculate_crc(body)
    return recv_crc == calc_crc or recv_crc == calc_crc[::-1]

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

# db_manager.py 맨 아래에 추가

METER_FIELDS = [
    "main_active", "main_reactive", 
    "ind_mid", "ind_max", "ind_light", 
    "street_mid", "street_max", "street_light", 
    "geo_1", "geo_2", "geo_3"
]

def create_manual_meter_table():
    """3개 계량장치의 일일 지침을 저장할 독자적인 테이블을 생성합니다."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS manual_meter_logs (
            log_date DATE PRIMARY KEY,
            main_active REAL,
            main_reactive REAL,
            ind_mid REAL,
            ind_max REAL,
            ind_light REAL,
            street_mid REAL,
            street_max REAL,
            street_light REAL,
            geo_1 REAL,
            geo_2 REAL,
            geo_3 REAL
        )
    ''')
    conn.commit()
    conn.close()

def get_manual_meter_data(target_date):
    """지정된 날짜의 수동 검침 지침 데이터를 딕셔너리 형태로 불러옵니다."""
    create_manual_meter_table() # 테이블 없으면 자동 생성
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    fields_str = ", ".join(METER_FIELDS)
    c.execute(f'SELECT {fields_str} FROM manual_meter_logs WHERE log_date = ?', (target_date,))
    res = c.fetchone()
    conn.close()
    
    data_dict = {f: "" for f in METER_FIELDS}
    if res:
        for idx, field in enumerate(METER_FIELDS):
            data_dict[field] = str(res[idx]) if res[idx] is not None else ""
    return data_dict

def save_manual_meter_data(target_date, data_dict):
    """지정된 날짜에 11개 필드 데이터를 저장하거나 기존 데이터가 있으면 수정(UPDATE)합니다."""
    create_manual_meter_table()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # INSERT OR REPLACE 구문을 활용하여 데이터 유무에 따라 저장/수정 자동 처리
    fields_str = "log_date, " + ", ".join(METER_FIELDS)
    placeholders = ", ".join(["?"] * (len(METER_FIELDS) + 1))
    
    values = [target_date]
    for field in METER_FIELDS:
        val = data_dict.get(field, "")
        values.append(float(val) if val.strip() != "" else None)
        
    c.execute(f'INSERT OR REPLACE INTO manual_meter_logs ({fields_str}) VALUES ({placeholders})', values)
    conn.commit()
    conn.close()