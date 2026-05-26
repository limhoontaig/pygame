# main.py
import sys
import threading
import time
from PyQt5.QtWidgets import QApplication, QSplashScreen, QDesktopWidget
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QCursor, QFont

# 최상위 관리 모듈 및 메인 UI 윈도우 로드
import db_manager
import plc_worker
from ui_main_window import SCADAWindow 

def center_window(widget):
    """위젯을 화면 중앙으로 이동시키는 함수"""
    qr = widget.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    widget.move(qr.topLeft())

if __name__ == "__main__":
    # 1. GUI 애플리케이션 생성
    app = QApplication(sys.argv)
    
    # 2. 로딩 화면(Splash Screen) 설정 및 크기 키우기
    splash = QSplashScreen()
    splash.setFixedSize(600, 400)
    splash.setStyleSheet("""
        QSplashScreen {
            background-color: #2c3e50;
            color: white;
            border: 3px solid #34495e;
            border-radius: 15px;
        }
    """)
    
    font = QFont("Malgun Gothic", 18, QFont.Bold)
    splash.setFont(font)
    
    # 화면 중앙에 배치하고 표시
    center_window(splash)
    splash.show()
    splash.raise_()
    
    # 마우스 커서를 '대기 상태'로 변경
    app.setOverrideCursor(QCursor(Qt.WaitCursor))
    
    # [개선] 텍스트가 잘 보이도록 정렬 및 줄바꿈 조정
    splash.showMessage("\n\n\n\n⚡ 시스템 엔진 기동 중...\n변전실 데이터를 불러오고 있습니다.", 
                       Qt.AlignCenter | Qt.AlignVCenter, Qt.white)
    
    # ⭐ [핵심 개선 1] OS가 로딩 창을 즉시 그릴 수 있도록 이벤트를 강제로 강하게 처리
    for _ in range(10):
        QCoreApplication.processEvents()
        time.sleep(0.05)  # 약 0.5초간 UI가 안정적으로 먼저 뜨도록 대기

    # 3. 데이터베이스 및 스레드 초기화
    # 이제 로딩 창이 완전히 뜬 상태에서 DB 작업을 시작하므로 사용자가 텍스트를 볼 수 있습니다.
    db_manager.init_db()
    
    # DB 초기화 직후 UI 갱신 한 번 더 실행
    QCoreApplication.processEvents()
    
    t = threading.Thread(target=plc_worker.serial_receive_thread, daemon=True)
    t.start()
    
    # 4. 메인 윈도우 생성
    win = SCADAWindow()
    
    # 5. 메인 화면 위치 및 포커스 설정
    center_window(win)
    
    # 다른 창들보다 가장 앞으로 강제로 띄우는 설정
    win.setWindowFlags(win.windowFlags() | Qt.WindowStaysOnTopHint)
    win.show()
    
    # 실행 직후 최상단 고정을 해제
    win.setWindowFlags(win.windowFlags() & ~Qt.WindowStaysOnTopHint) 
    win.show()
    
    # 최종적으로 포커스를 줌
    win.raise_()
    win.activateWindow()
    
    # 로딩 창 종료 및 커서 복구
    splash.finish(win)
    app.restoreOverrideCursor()
    
    sys.exit(app.exec_())