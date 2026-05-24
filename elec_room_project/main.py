# main.py
import sys
import threading
from PyQt5.QtWidgets import QApplication

# 최상위 관리 모듈 및 메인 UI 윈도우 로드
import db_manager
import plc_worker
from ui_main_window import SCADAWindow # 💡 분리한 메인 윈도우 임포트

if __name__ == "__main__":
    # 1. 데이터베이스 초기화
    db_manager.init_db()

    # 2. PLC 데이터 수신 백그라운드 스레드 가동
    t = threading.Thread(target=plc_worker.serial_receive_thread, daemon=True)
    t.start()
    
    # 3. GUI 애플리케이션 실행
    app = QApplication(sys.argv)
    win = SCADAWindow()
    win.show()
    sys.exit(app.exec_())