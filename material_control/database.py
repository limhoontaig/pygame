# database.py
import pymysql
import pandas as pd
import os
import hashlib

def hash_password(password):
    """비밀번호를 SHA-256 방식으로 안전하게 암호화합니다."""
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    """
    💡 [수정] SQLite 파일 연결 대신, 내 PC(localhost)에 설치된 MariaDB 서버에 접속합니다.
    """
    conn = pymysql.connect(
        host="127.0.0.1",         # 내 PC에 설치된 DB 서버를 가리킴
        user="root",              # MariaDB 기본 최고 관리자 계정
        password="4523",   # ⚠️ MariaDB 설치할 때 비밀번호 적어주세요!
        database="inventory_db",  # 하이디SQL에서 새로 만든 데이터베이스 이름
        port=3306,                # MariaDB 기본 포트 번호
        charset="utf8mb4",        # 한글 깨짐 방지 인코딩
        autocommit=True           # 데이터 입력/수정 시 즉시 반영 설정
    )
    return conn

# database.py 파일 내부의 init_database 함수를 아래 내용으로 교체하거나 보완합니다.

# database.py 파일 내부의 init_database 함수를 아래 내용으로 교체하거나 보완합니다.

def init_database():
    """
    MariaDB 문법에 맞추어 모든 필수 테이블(마스터 테이블 포함)을 생성합니다.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 자재 입고 대장 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inbound_ledger (
            id INT PRIMARY KEY AUTO_INCREMENT,
            in_date VARCHAR(20) NOT NULL,
            discipline VARCHAR(50),
            item_name VARCHAR(200) NOT NULL,
            spec VARCHAR(200),
            qty INT DEFAULT 0,
            total_price INT DEFAULT 0,
            unit_price INT DEFAULT 0,
            supplier VARCHAR(100),
            remarks TEXT,
            worker VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. 자재 사용 대장 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_ledger (
            id INT PRIMARY KEY AUTO_INCREMENT,
            use_date VARCHAR(20) NOT NULL,
            usage_type VARCHAR(50) NOT NULL,
            dong VARCHAR(20),
            ho VARCHAR(20),
            discipline VARCHAR(50),
            item_name VARCHAR(200) NOT NULL,
            spec VARCHAR(200),
            qty INT DEFAULT 0,
            remarks TEXT,
            worker VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. 🌟 [추가/보완] 자재 마스터 테이블 (에러 원인 해결)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS material_items (
            id INT PRIMARY KEY AUTO_INCREMENT,
            item_name VARCHAR(200) NOT NULL,
            spec VARCHAR(200),
            UNIQUE(item_name, spec)
        )
    """)
    
    # 4. 🌟 [추가/보완] 동호수 마스터 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dongho_master (
            id INT PRIMARY KEY AUTO_INCREMENT,
            dong VARCHAR(20) NOT NULL,
            ho VARCHAR(20) NOT NULL,
            UNIQUE(dong, ho)
        )
    """)
    
    # 5. 사용자 계정 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            status VARCHAR(20) DEFAULT 'PENDING',
            is_admin INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 기본 관리자 계정(admin) 자동 생성
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        admin_pw = hash_password('admin1234')
        cursor.execute("""
            INSERT INTO users (username, password, status, is_admin) 
            VALUES ('admin', %s, 'APPROVED', 1)
        """, (admin_pw,))
        print("[시스템 알림]: 기본 관리자 계정(admin / admin1234)이 생성되었습니다.")

    # (주의: 동호수 엑셀 로드 로직은 SQLite 문법(?)이 섞여 있을 수 있으므로 
    #  안전한 테이블 생성을 위해 우선 이 단계까지만 확실히 실행합니다.)
    conn.commit()
    conn.close()
    print("[시스템 알림]: 모든 마스터 및 대장 테이블 스키마 초기화 완료.")

def get_current_stock(item_name, spec):
    """
    💡 [수정] 변수 바인딩 기호를 SQLite(?)에서 MariaDB(%s)로 변경하여 실시간 재고를 산출합니다.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 입고량 총합 구하기
    cursor.execute("SELECT SUM(qty) FROM inbound_ledger WHERE item_name = %s AND spec = %s", (item_name, spec))
    total_in = cursor.fetchone()[0] or 0
    
    # 2. 사용량 총합 구하기 (기존 소스 중복 함수 제거 및 정리)
    cursor.execute("SELECT SUM(qty) FROM usage_ledger WHERE item_name = %s AND spec = %s", (item_name, spec))
    total_out = cursor.fetchone()[0] or 0
    
    conn.close()
    return total_in - total_out