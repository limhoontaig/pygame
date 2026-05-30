import sys
from PyQt5.QtWidgets import QApplication, QDialog
import database
from login_dialog import LoginDialog
from material_main import MainApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 1. 시스템 DB 초기화 (테이블이 없으면 자동 생성)
    database.init_database()
    
    # 2. 로그인 화면 실행
    login = LoginDialog()
    
    if login.exec_() == QDialog.Accepted:
        # 로그인 성공 시 선택된 사용자명 획득
        user_name = login.get_logged_in_user()
        
        # 3. 메인 윈도우 생성 시 유저명 전달 후 실행
        main_win = MainApp(user_name=user_name)
        main_win.show()
        
        sys.exit(app.exec_())
    else:
        # 로그인 취소 시 종료
        sys.exit(0)