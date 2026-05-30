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

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 자재 입고 대장 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inbound_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            in_date TEXT NOT NULL,
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
    
    # 2. 자재 마스터 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS material_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            spec TEXT NOT NULL,
            UNIQUE(item_name, spec)
        )
    """)
    
    # 3. 사용자 정보 테이블 [구조 수정]
    # status: 'PENDING'(대기), 'APPROVED'(승인), 'REJECTED'(거절)
    # is_admin: 1(관리자), 0(일반사용자)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            is_admin INTEGER DEFAULT 0
        )
    """)
    
    # 기본 초기 데이터 세팅 (자재 마스터)
    cursor.execute("SELECT COUNT(*) FROM material_items")
    if cursor.fetchone()[0] == 0:
        default_materials = [("램프", "LED 10W")]
        cursor.executemany("INSERT OR IGNORE INTO material_items (item_name, spec) VALUES (?, ?)", default_materials)
        
    # 기본 관리자 계정 생성 (최초 테이블이 비었을 때 '관리자' 자동 생성)
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
    if cursor.fetchone()[0] == 0:
        admin_pw_hash = hash_password("admin123") # 기본 초기 비밀번호: admin123
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, status, is_admin) 
            VALUES (?, ?, ?, ?)
        """, ('admin', admin_pw_hash, 'APPROVED', 1))

    # 4. 자재 사용(출고) 대장 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outbound_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            out_date TEXT NOT NULL,
            dong TEXT,
            ho TEXT,
            category TEXT,
            item_name TEXT NOT NULL,
            spec TEXT,
            qty INTEGER NOT NULL,
            remarks TEXT,
            worker TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 5. 동호 마스터 테이블
    cursor.execute("CREATE TABLE IF NOT EXISTS dongho_master (dong TEXT, ho TEXT)")
    
    cursor.execute("SELECT COUNT(*) FROM dongho_master")
    if cursor.fetchone()[0] == 0:
        file_name = "동호인덱스.xlsx"
        excel_file = os.path.join(BASE_DIR, "data", file_name)
        
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

def get_current_stock(item_name, spec):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(qty) FROM inbound_ledger WHERE item_name = ? AND spec = ?", (item_name, spec))
    total_in = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(qty) FROM outbound_ledger WHERE item_name = ? AND spec = ?", (item_name, spec))
    total_out = cursor.fetchone()[0] or 0
    
    conn.close()
    return total_in - total_out