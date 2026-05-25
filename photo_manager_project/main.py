# main.py
import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

def resource_path(relative_path):
    """실행 파일 빌드 시 리소스 경로를 처리하는 헬퍼 함수"""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # ui 폴더 내부에 위치할 UI 파일 경로 지정
    ui_path = resource_path(os.path.join("ui", "pictures_control.ui"))
    
    # 메인 윈도우 생성 및 실행
    main_window = MainWindow(ui_path)
    main_window.show()
    
    sys.exit(app.exec_())