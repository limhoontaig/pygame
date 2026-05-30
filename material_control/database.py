# database.py
import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "material_management.db")

def get_db_connection():
    # 프로그램을 실행하면 터미널 창에 실제 DB 파일의 절대 경로가 찍힙니다.
    print(f"[DB 접속 경로 확인]: {DB_NAME}")
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
            item_name TEXT NOT NULL,  -- 품명 (예: 램프)
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
            ("램프", "LED 10W")
        ]
        cursor.executemany("INSERT OR IGNORE INTO material_items (item_name, spec) VALUES (?, ?)", default_materials)
        
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO users (username) VALUES (?)", [('관리자',), ('홍길동',), ('김철수',)])

    # 4. [추가] 자재 사용(출고) 대장 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outbound_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            out_date TEXT NOT NULL,         -- 사용일자
            dong TEXT,                      -- 동
            ho TEXT,                        -- 호
            category TEXT,                  -- 구분 (공용/세대)
            item_name TEXT NOT NULL,        -- 품명
            spec TEXT,                      -- 규격
            qty INTEGER NOT NULL,           -- 사용수량
            remarks TEXT,                   -- 비고
            worker TEXT NOT NULL,           -- 입력자
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 5. [추가] 동호 마스터 테이블 (엑셀에서 읽어올 데이터)
    cursor.execute("CREATE TABLE IF NOT EXISTS dongho_master (dong TEXT, ho TEXT)")
    
    # 동호 데이터 임포트 (테이블이 비었을 때만 수행)
    cursor.execute("SELECT COUNT(*) FROM dongho_master")
    if cursor.fetchone()[0] == 0:
        
        # [수정] data 폴더 안의 파일 경로를 절대 경로로 안전하게 결합합니다.
        file_name = "동호인덱스.xlsx"
        excel_file = os.path.join(BASE_DIR, "data", file_name)
        
        print(f"찾고 있는 파일의 절대 경로: {excel_file}") # 디버깅 확인용 출력
        
        if os.path.exists(excel_file):
            try:
                # 파일 확장자에 따라 판다스 읽기 분기
                if excel_file.endswith('.csv'):
                    df = pd.read_csv(excel_file)
                else:
                    df = pd.read_excel(excel_file)
                
                # 컬럼명 자동 매칭 (실제 컬럼명이 '동', '호'가 아닐 경우를 대비)
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
                else:
                    print("오류: 파일 안에서 '동' 또는 '호' 컬럼을 찾을 수 없습니다.")
                    
            except Exception as e:
                print(f"데이터 로드 오류: {e}")
        else:
            # [안내] 어디가 잘못되었는지 터미널창에서 명확하게 확인할 수 있습니다.
            print(f"오류: '{file_name}' 파일이 지정된 경로에 존재하지 않습니다.")
            print(f"실제 파일을 다음 위치에 놓아주세요: {os.path.join(BASE_DIR, 'data')}")

    conn.commit()
    conn.close()

def get_current_stock(item_name, spec):
    """특정 품명과 규격의 현재 재고 수량을 계산하여 반환합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 총 입고량 계산
    cursor.execute("""
        SELECT SUM(qty) FROM inbound_ledger 
        WHERE item_name = ? AND spec = ?
    """, (item_name, spec))
    total_in = cursor.fetchone()[0] or 0
    
    # 2. 총 사용(출고)량 계산
    cursor.execute("""
        SELECT SUM(qty) FROM outbound_ledger 
        WHERE item_name = ? AND spec = ?
    """, (item_name, spec))
    total_out = cursor.fetchone()[0] or 0
    
    conn.close()
    
    # 현재 재고 = 입고량 - 출고량
    return total_in - total_out