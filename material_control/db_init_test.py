# db_init_test.py (테이블 강제 생성용 임시 파일)
import database

print("1. 마리아DB 연결 및 테이블 생성을 시작합니다...")
try:
    # database.py에 있는 초기화 함수를 강제로 실행합니다.
    database.init_database()
    print("✅ 2. 테이블 생성 로직이 에러 없이 끝났습니다!")
    print("이제 하이디SQL로 돌아가서 F5(새로고침)를 눌러보세요.")
except Exception as e:
    print(f"❌ 오류 발생: 테이블을 만드는 중 에러가 났습니다.\n오류 내용: {e}")