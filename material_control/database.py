# database.py

# database.py
import sqlite3
import pandas as pd
import os
import hashlib  # 비밀번호 암호화를 위해 추가

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "material_management.db")

def hash_password(password):
    """비밀번호를 SHA-256 방식으로 안전하게 암호화합니다."""
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    print(f"[DB 접속 경로 확인]: {DB_NAME}")
    return sqlite3.connect(DB_NAME)

# database.py
import sqlite3
import pandas as pd
import os
import hashlib  # 비밀번호 암호화를 위해 추가

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "material_management.db")

def hash_password(password):
    """비밀번호를 SHA-256 방식으로 안전하게 암호화합니다."""
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    # print(f\"[DB 접속 경로 확인]: {DB_NAME}\")
    return sqlite3.connect(DB_NAME)

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 자재 입고 대장 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inbound_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            in_date TEXT NOT NULL,
            discipline TEXT,
            item_name TEXT NOT NULL,
            spec TEXT,
            qty INTEGER DEFAULT 0,
            total_price INTEGER DEFAULT 0,
            unit_price INTEGER DEFAULT 0,
            supplier TEXT,
            remarks TEXT,
            worker TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. [추가] 자재 사용 대장 테이블 (usage_ledger 공종 discipline 반영)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            use_date TEXT NOT NULL,
            usage_type TEXT NOT NULL,  -- 세대 / 공용
            dong TEXT,
            ho TEXT,
            discipline TEXT,           -- 공종 컬럼 추가
            item_name TEXT NOT NULL,
            spec TEXT,
            qty INTEGER DEFAULT 0,
            remarks TEXT,
            worker TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. 자재 마스터 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS material_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            spec TEXT,
            UNIQUE(item_name, spec)
        )
    """)
    
    # 4. 동호수 마스터 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dongho_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dong TEXT NOT NULL,
            ho TEXT NOT NULL,
            UNIQUE(dong, ho)
        )
    """)
    
    # 5. 사용자 계정 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 기본 관리자 계정(admin) 자동 생성 (없을 경우만)
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        admin_pw = hash_password('admin1234')
        cursor.execute("""
            INSERT INTO users (username, password, status, is_admin) 
            VALUES ('admin', ?, 'APPROVED', 1)
        """, (admin_pw,))
        print("[시스템 알림]: 기본 관리자 계정(admin / admin1234)이 생성되었습니다.")

    # 6. 동호수 엑셀 데이터 초기 로드 로직 (기존 소스 유지)
    cursor.execute("SELECT COUNT(*) FROM dongho_master")
    if cursor.fetchone()[0] == 0:
        excel_file = os.path.join(BASE_DIR, "동호수_마스터.xlsx")
        if not os.path.exists(excel_file):
            excel_file = os.path.join(BASE_DIR, "동호수_마스터.csv")
            
        if os.path.exists(excel_file):
            try:
                if excel_file.endswith('.csv'):
                    df = pd.read_csv(excel_file)
                else:
                    df = pd.read_excel(excel_file)
                
                dong_col = [c for c in df.columns if '동' in str(c)]
                ho_col = [c for c in df.columns if '호' in str(c)]
                
                if dong_col and ho_col:
                    target_dong = dong_col[0]
                    target_ho = ho_col[0]
                    df[[target_dong, target_ho]] = df[[target_dong, target_ho]].astype(str)
                    
                    for _, row in df.iterrows():
                        cursor.execute(
                            "INSERT INTO dongho_master (dong, ho) VALUES (?, ?)", 
                            (row[target_dong].strip(), row[target_ho].strip())
                        )
                    print(f"총 {len(df)}건의 동호 데이터를 DB로 로드했습니다.")
            except Exception as e:
                print(f"데이터 로드 오류: {e}")

    conn.commit()
    conn.close()
    print("[시스템 알림]: 데이터베이스 테이블 스키마 초기화 완료.")

def get_current_stock(item_name, spec):
    """현재 재고를 산출합니다. (입고량 합계 - 사용량 합계)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 입고량 총합
    cursor.execute("SELECT SUM(qty) FROM inbound_ledger WHERE item_name = ? AND spec = ?", (item_name, spec))
    total_in = cursor.fetchone()[0] or 0
    
    # 사용량 총합
    cursor.execute("SELECT SUM(qty) FROM usage_ledger WHERE item_name = ? AND spec = ?", (item_name, spec))
    total_out = cursor.fetchone()[0] or 0
    
    conn.close()
    return total_in - total_out

def get_current_stock(item_name, spec):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(qty) FROM inbound_ledger WHERE item_name = ? AND spec = ?", (item_name, spec))
    total_in = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(qty) FROM outbound_ledger WHERE item_name = ? AND spec = ?", (item_name, spec))
    total_out = cursor.fetchone()[0] or 0
    
    conn.close()
    return total_in - total_out