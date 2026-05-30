# database.py
import sqlite3

DB_NAME = "material_management.db"

def get_db_connection():
    return sqlite3.connect(DB_NAME)

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 자재 입고 대장 테이블 (동일)
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
    
    # 2. ★ [추가] 자재 마스터 테이블 (콤보박스 연동용)
    # 품명과 규격의 쌍을 고유(UNIQUE)하게 묶어 중복 등록을 방지합니다.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS material_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,  -- 품명 (예: 전구/램프)
            spec TEXT NOT NULL,       -- 규격 (예: LED 10W)
            UNIQUE(item_name, spec)   -- 중복 방지 제약조건
        )
    """)
    
    # 3. 사용자 정보 테이블 (동일)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY)
    """)
    
    # 기본 초기 데이터 세팅 (자재 마스터 테이블이 비어있을 때만 기본값 주입)
    cursor.execute("SELECT COUNT(*) FROM material_items")
    if cursor.fetchone()[0] == 0:
        default_materials = [
            ("전구/램프", "LED 10W"),
            ("전구/램프", "LED 20W"),
            ("배관자재", "PVC 파이프 50A"),
            ("밸브류", "볼밸브 15A")
        ]
        cursor.executemany("INSERT OR IGNORE INTO material_items (item_name, spec) VALUES (?, ?)", default_materials)
        
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO users (username) VALUES (?)", [('관리자',), ('홍길동',), ('김철수',)])
        
    conn.commit()
    conn.close()