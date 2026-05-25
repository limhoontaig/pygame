# config.py

# MySQL 데이터베이스 접속 정보 설정
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password_here',  # 실제 비밀번호를 입력하세요.
    'database': 'your_database_name'   # 실제 DB 이름을 입력하세요.
}

# 대용량 사진 처리용 지원 확장자 정의
SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.mp4', '.avi', '.mov', '.mkv')