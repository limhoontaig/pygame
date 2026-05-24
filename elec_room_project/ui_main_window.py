# ui_main_window.py
import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QDateEdit, QPushButton, QStackedWidget, QSplitter, 
                             QTableWidget, QTableWidgetItem, QComboBox, QListWidget, QAbstractItemView, QMessageBox, QFileDialog)
from PyQt5.QtCore import QTimer, QDate, Qt

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# 커스텀 기능 및 팝업창 모듈 로드
import db_manager
import excel_report
from ui_dialogs import ManualMeterInputDialog # 💡 분리한 팝업창 임포트

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

class SCADAWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(10000) 
        self.last_hour = datetime.now().hour

    def initUI(self):
        self.setWindowTitle("래미안개포루체하임아파트 변전실 데이터 통합 관리 시스템 (모듈화 프로젝트)")
        self.resize(1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        top_ctrl = QGroupBox("운영 제어 센터")
        top_layout = QHBoxLayout(top_ctrl)
        top_layout.setSpacing(50)
        
        self.qdate = QDateEdit(QDate.currentDate())
        self.qdate.setCalendarPopup(True)
        
        lbl_date_title = QLabel("<b>선택 날짜:</b>")
        lbl_date_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_date_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        top_layout.addWidget(lbl_date_title)
        
        top_layout.addWidget(self.qdate)

        self.qdate.setMinimumWidth(120) # 가로 최소 크기를 150 픽셀로 강제 확장 (기존보다 훨씬 넓어집니다)
        self.qdate.setAlignment(Qt.AlignCenter) # 날짜 글자를 가운데 정렬하여 가독성 향상
        self.qdate.setStyleSheet("font-size: 14px; padding: 3px; font-weight: bold;") # 글자 크기 및 내부 여백 조정
        
        self.btn_show_table = QPushButton("종합 데이터 표")
        self.btn_show_table.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; min-height: 35px;")
        self.btn_show_graph = QPushButton("부하 변동 그래프")
        self.btn_show_graph.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; min-height: 35px;")
        self.btn_export_excel = QPushButton("엑셀 운영일지 출력")
        self.btn_export_excel.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; min-height: 35px;")
        
        # SCADAWindow 클래스의 initUI 또는 버튼 레이아웃 배치 구역에 추가
        self.btn_meter_input = QPushButton("전력량계 검침량 입력") # 요청하신 버튼명 지정
        self.btn_meter_input.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; min-height: 35px;")
        self.btn_meter_input.clicked.connect(self.click_open_meter_popup)
        
        top_layout.addWidget(self.btn_show_table)
        top_layout.addWidget(self.btn_show_graph)
        top_layout.addWidget(self.btn_export_excel)
        # 🛠️ 수정한 부분: hbox 대신 top_layout 레이아웃 변수명을 정확하게 매칭
        top_layout.addWidget(self.btn_meter_input)    
        main_layout.addWidget(top_ctrl)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # 테이블 탭 구성
        self.page_table = QWidget()
        table_layout = QVBoxLayout(self.page_table)
        splitter = QSplitter(Qt.Vertical)
        
        self.raw_table = QTableWidget()
        self.raw_table.setColumnCount(len(db_manager.COLUMN_LABELS))
        self.raw_table.setHorizontalHeaderLabels(db_manager.COLUMN_LABELS)
        
        self.avg_table = QTableWidget()
        self.avg_table.setColumnCount(len(db_manager.COLUMN_LABELS))
        self.avg_table.setHorizontalHeaderLabels(db_manager.COLUMN_LABELS)

        self.extreme_table = QTableWidget()
        self.extreme_table.setColumnCount(len(db_manager.COLUMN_LABELS))
        self.extreme_table.setHorizontalHeaderLabels(db_manager.COLUMN_LABELS)

        # 🛠️ [새로운 추가 항목] 수동 계량기 일지 로그 테이블 설계
        self.manual_table = QTableWidget()
        manual_headers = ["기록 일자"] + db_manager.METER_FIELDS # 날짜 + 11개 수동필드 제목 매칭
        self.manual_table.setColumnCount(len(manual_headers))
        self.manual_table.setHorizontalHeaderLabels(manual_headers)

        splitter.addWidget(QLabel("● 실시간 계측 데이터 로그"))
        splitter.addWidget(self.raw_table)
        splitter.addWidget(QLabel("● 시간별 평균 전력 추이"))
        splitter.addWidget(self.avg_table)
        splitter.addWidget(QLabel("● 일일 최고(MAX) / 최저(MIN) 값 설비 통계"))
        splitter.addWidget(self.extreme_table)

        # 🛠️ 분할 스플리터 레이아웃에 수동 지침 데이터 표 안착
        splitter.addWidget(QLabel("● 독립 계량장치 일일 지침 수동 로그 (manual_meter_logs)"))
        splitter.addWidget(self.manual_table)


        table_layout.addWidget(splitter)
        self.stack.addWidget(self.page_table)

        # 그래프 탭 구성
        self.page_graph = QWidget()
        graph_layout = QVBoxLayout(self.page_graph)
        
        graph_ctrl = QHBoxLayout()
        
        '''
        self.data_selector = QComboBox()
        '''
        # 변경: 단일 선택 콤보박스 대신, 다중 선택이 가능한 QListWidget 사용
        from PyQt5.QtWidgets import QListWidget, QAbstractItemView
        self.data_selector = QListWidget()
        self.data_selector.setSelectionMode(QAbstractItemView.MultiSelection) # 다중 선택 모드 활성화
        self.data_selector.addItems(db_manager.DATA_LABELS)
        self.data_selector.setMaximumHeight(80) # UI 공간을 너무 차지하지 않도록 높이 제한
        
        # 기본적으로 첫 번째 항목은 선택되어 있도록 설정
        if self.data_selector.count() > 0:
            self.data_selector.item(0).setSelected(True)
        
        
        # self.data_selector.addItems(db_manager.DATA_LABELS)
        self.period_selector = QComboBox()
        self.period_selector.addItems(["일간 (실시간 데이터)", "주간 (시간별 평균)", "월간 (시간별 평균)"])
        
        graph_ctrl.addWidget(QLabel("시각화 필드:"))
        graph_ctrl.addWidget(self.data_selector)
        graph_ctrl.addWidget(QLabel("조회 기간:"))
        graph_ctrl.addWidget(self.period_selector)
        graph_layout.addLayout(graph_ctrl)

        self.canvas = FigureCanvas(Figure(figsize=(8, 5)))
        self.ax = self.canvas.figure.add_subplot(111)
        graph_layout.addWidget(self.canvas)
        self.stack.addWidget(self.page_graph)

        self.btn_show_table.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_show_graph.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        # 💡 분리해 둔 엑셀 엔진 모듈의 함수를 바로 호출합니다!
        self.btn_export_excel.clicked.connect(self.export_excel_click)
        
        self.qdate.dateChanged.connect(self.auto_refresh)
        # currentIndexChanged 대신 itemSelectionChanged를 사용합니다.
        self.data_selector.itemSelectionChanged.connect(self.update_graph)
        # self.data_selector.currentIndexChanged.connect(self.update_graph)
        self.period_selector.currentIndexChanged.connect(self.update_graph)

        self.load_data()

    def load_data(self):
        selected_date = self.qdate.date().toString("yyyy-MM-dd")
        db_manager.calculate_daily_extremes(selected_date)
        
        try:
            conn = sqlite3.connect(db_manager.DB_NAME)
            c = conn.cursor()
            
            query_raw = f"SELECT log_date, log_time, {', '.join([f'\"{n}\"' for n in db_manager.DATA_LABELS])} FROM raw_data WHERE log_date = ? ORDER BY log_time DESC" # LIMIT 50"
            c.execute(query_raw, (selected_date,))
            self.display_table(self.raw_table, c.fetchall())
            
            query_avg = f"SELECT log_date, log_time, {', '.join([f'\"{n}\"' for n in db_manager.DATA_LABELS])} FROM hourly_avg WHERE log_date = ? ORDER BY log_time ASC"
            c.execute(query_avg, (selected_date,))
            self.display_table(self.avg_table, c.fetchall())
            
            query_ext = f"SELECT log_date, extreme_type, {', '.join([f'\"{n}\"' for n in db_manager.DATA_LABELS])} FROM daily_extremes WHERE log_date = ? ORDER BY extreme_type DESC"
            c.execute(query_ext, (selected_date,))
            self.display_table(self.extreme_table, c.fetchall(), is_extreme=True)
            
            conn.close()

            # 🛠️ 수동 입력 로그 조회 연동 추가
            if hasattr(db_manager, 'get_manual_meter_log_for_table'):
                manual_row = db_manager.get_manual_meter_log_for_table(selected_date)
                self.display_manual_table([manual_row])

        except Exception as e:
            print(f"UI 로딩 실패: {e}")

    # 🛠️ 수동 검침 출력 전용 가벼운 렌더링 함수
    def display_manual_table(self, rows):
        self.manual_table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                # 수동 데이터 식별을 위해 연한 노란색/청색 계열 텍스트 포인트 추가 가능
                if c_idx > 0 and val != "-":
                    item.setForeground(Qt.darkGreen)
                self.manual_table.setItem(r_idx, c_idx, item)


    def update_graph(self):
        if self.stack.currentIndex() != 1: return
        
        # 1. 선택된 모든 필드 가져오기
        selected_items = self.data_selector.selectedItems()
        if not selected_items:
            self.ax.clear()
            self.ax.text(0.5, 0.5, "비교할 필드를 선택해주세요.", ha='center')
            self.canvas.draw()
            return
            
        target_cols = [item.text() for item in selected_items]
        period = self.period_selector.currentText()
        selected_date = self.qdate.date().toPyDate()

        # 2. SQL 쿼리문 생성 (선택된 모든 필드를 콤마로 연결하여 호출)
        cols_str = ', '.join([f'"{col}"' for col in target_cols])
        
        conn = sqlite3.connect(db_manager.DB_NAME)
        if "일간" in period:
            query = f'SELECT log_time, {cols_str} FROM raw_data WHERE log_date = ? ORDER BY log_time ASC'
            params = (selected_date.strftime('%Y-%m-%d'),)
        else:
            days = 7 if "주간" in period else 30
            start_date = selected_date - timedelta(days=days)
            query = f'SELECT log_date || \' \' || SUBSTR(log_time,1,5) as dt, {cols_str} FROM hourly_avg WHERE log_date BETWEEN ? AND ? ORDER BY log_date, log_time'
            params = (start_date.strftime('%Y-%m-%d'), selected_date.strftime('%Y-%m-%d'))

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        # 3. 그래프 그리기 (다중 선 구현)
        self.ax.clear()
        if not df.empty:
            x_col = 'log_time' if "일간" in period else 'dt'
            
            # 선택한 필드 수만큼 반복하며 그래프에 선을 누적해서 그립니다.
            for col in target_cols:
                self.ax.plot(df[x_col], df[col], marker='o', markersize=2, label=col)
                
            import matplotlib.ticker as ticker
            self.ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
            self.ax.set_title(f"선택 필드 {period} 비교 분석")
            self.ax.grid(True, linestyle='--')
            self.ax.legend(loc='upper right') # 각 선이 무엇인지 알려주는 범례 표시
            self.canvas.figure.autofmt_xdate() 
        else:
            self.ax.text(0.5, 0.5, "데이터가 존재하지 않습니다.", ha='center')
        
        self.canvas.draw()

    def display_table(self, table, rows, is_extreme=False):
        table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                txt = f"{val:.1f}" if isinstance(val, float) else str(val)
                item = QTableWidgetItem(txt)
                # 💡 이 줄을 추가하여 모든 텍스트를 중앙 정렬합니다.
                item.setTextAlignment(Qt.AlignCenter)

                if is_extreme and c_idx > 1:
                    if row[1] == 'MAX': item.setForeground(Qt.red)
                    elif row[1] == 'MIN': item.setForeground(Qt.blue)
                table.setItem(r_idx, c_idx, item)

    def export_excel_click(self):
        selected_date = self.qdate.date().toString("yyyy-MM-dd")
        
        # 1. 사용자에게 저장할 디렉토리 경로를 입력받는 표준 대화상자 팝업
        selected_dir = QFileDialog.getExistingDirectory(self, "운영일지 저장 폴더 선택", "")
        
        # 2. 사용자가 폴더를 선택하지 않고 취소(창닫기)했을 경우 처리
        if not selected_dir:
            return  # 프로세스 안전 종료 (아무 작업도 하지 않음)
            
        try:
            # 3. 엑셀 생성 엔진에 선택된 디렉토리 경로를 함께 전달
            # (excel_report.py의 함수가 target_dir 매개변수를 받도록 함께 수정해야 합니다)
            excel_report.generate_excel_report(selected_date, target_dir=selected_dir)
            
            # 4. 저장 성공 완료 알림창 표시
            saved_path = os.path.join(selected_dir, f"{selected_date}_전기실_운영일지.xlsx")
            QMessageBox.information(
                self, "출력 완료", 
                f"성공적으로 엑셀 운영일지가 생성되었습니다.\n\n저장 경로:\n{saved_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "출력 실패", f"에러 발생:\n{e}")

    def auto_refresh(self):
        curr_hour = datetime.now().hour
        if curr_hour != self.last_hour:
            db_manager.calculate_hourly_avg()
            self.last_hour = curr_hour
        self.load_data()
        self.update_graph()

    def click_open_meter_popup(self):
        """[수동 지침 입력] 버튼 클릭 시 호출되는 함수 (QDialog 임포트 에러 해결 버전)"""
        print("\n=== [DEBUG] 1. 수동 입력 팝업 창 생성 시작 ===")
        current_date_str = self.qdate.date().toString("yyyy-MM-dd") # 변수명 self.qdate 반영 완료
        
        # 팝업 객체 생성 및 실행
        dialog = ManualMeterInputDialog(current_date_str, self)
        print("=== [DEBUG] 2. 팝업 창 exec_() 실행 (사용자 입력 대기) ===")
        
        result = dialog.exec_()
        print(f"=== [DEBUG] 3. 팝업 창 닫힘 (반환 결과 코드: {result}) ===")
        
        # 💡 NameError를 방지하기 위해 정수 숫자(1 = Accepted, 0 = Rejected)로 명확하게 비교합니다.
        if result == 1: # 1은 QDialog.Accepted를 의미합니다.
            print("=== [DEBUG] 4. 사용자가 Save(저장)를 눌러 Accepted 블록 진입 ===")
            
            save_date = dialog.date_edit.date().toString("yyyy-MM-dd")
            print(f"    * 저장 대상 날짜: {save_date}")
            
            # 입력 데이터 수집
            final_data = {}
            try:
                for field, edit in dialog.inputs.items():
                    final_data[field] = edit.text().strip()
                print(f"    * 수집된 데이터 딕셔너리: {final_data}")
            except Exception as e:
                print(f"    ❌ [ERROR] 데이터 수집 중 에러 발생: {e}")
                return

            # 사용자에게 저장 여부 확인
            print("=== [DEBUG] 5. 저장 확인 메시지 박스 출력 직전 ===")
            reply = QMessageBox.question(
                self, '데이터 저장 확인',
                f"[{save_date}] 수동 입력 지침을 DB에 반영하시겠습니까?\n(Yes 선택 시 운영일지 출력이 함께 진행됩니다.)",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            print(f"    * 사용자의 선택 결과: {'Yes' if reply == QMessageBox.Yes else 'No'}")
            
            selected_dir = None
            if reply == QMessageBox.Yes:
                print("=== [DEBUG] 6. 엑셀 저장 폴더 선택 창 오픈 ===")
                selected_dir = QFileDialog.getExistingDirectory(self, "운영일지 저장 폴더 선택 (DB 저장 후 자동 출력)", "")
                print(f"    * 선택된 폴더 경로: {selected_dir}")
                if not selected_dir:
                    print("    ⚠️ [WARNING] 폴더 선택이 취소되어 작업을 중단합니다.")
                    QMessageBox.warning(self, "작업 취소", "폴더가 선택되지 않아 DB 저장 및 엑셀 출력 작업이 취소되었습니다.")
                    return

            try:
                print("=== [DEBUG] 7. db_manager.save_manual_meter_data 호출 직전 ===")
                db_manager.save_manual_meter_data(save_date, final_data)
                print("    * DB 저장 성공!")
                
                success_msg = f"[{save_date}] 일자의 데이터가 DB에 안전하게 반영되었습니다."
                
                if reply == QMessageBox.Yes and selected_dir:
                    print("=== [DEBUG] 8. excel_report.generate_excel_report 호출 직전 ===")
                    excel_report.generate_excel_report(save_date, target_dir=selected_dir)
                    saved_path = os.path.join(selected_dir, f"{save_date}_전기실_운영일지.xlsx")
                    success_msg += f"\n\n이어서 엑셀 운영일지 출력이 완료되었습니다.\n저장 경로:\n{saved_path}"
                    print("    * 엑셀 출력 성공!")
                
                QMessageBox.information(self, "저장 완료", success_msg)
                
                print("=== [DEBUG] 9. 메인 화면 테이블/그래프 새로고침(refresh_data) 호출 직전 ===")
                # 만약 메인윈도우 새로고침 함수명이 다르면 이 부분에서 에러가 날 수 있으니 주시해 주세요.
                if hasattr(self, 'refresh_data'):
                    self.refresh_data()
                elif hasattr(self, 'load_data'):
                    self.load_data()
                print("=== [DEBUG] 10. 모든 프로세스 정상 완료 ===")
                
            except Exception as e:
                print(f"    ❌ [ERROR] DB 저장 또는 엑셀 출력 중 예외 발생: {e}")
                QMessageBox.critical(self, "오류 발생", f"작업 중 에러가 발생했습니다:\n{str(e)}")
                
        else:
            # result가 0(Rejected, 취소)인 경우 일로 들어옵니다.
            print("=== [DEBUG] 4-Cancel. 사용자가 Cancel(취소)을 누르거나 창을 닫음 (Rejected) ===")
            print("=== [DEBUG] 5-Cancel. 추가 작업 없이 안전하게 함수 종료 ===")

    '''
    # 🛠️ 수동 검침 입력 팝업 함수 수정
    def click_open_meter_popup(self):
        """'전력량 입력' 버튼 터치 시 수동 검침 통합 팝업을 기동하고 저장/출력을 연동하는 함수"""
        current_view_date = self.qdate.date().toString("yyyy-MM-dd")
        
        dialog = ManualMeterInputDialog(current_view_date, self)
        if dialog.exec_() == QDialog.Accepted:
            save_date, final_data = dialog.get_final_inputs()
            
            # 1. 엑셀 운영일지 함께 출력 여부 확인 질의 창
            reply = QMessageBox.question(
                self, "엑셀 동시 출력 확인",
                f"[{save_date}] 일자의 데이터를 DB에 저장합니다.\n이와 동시에 엑셀 운영일지도 함께 출력하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            
            selected_dir = None
            # 2. 'Yes'인 경우 저장 전에 디렉토리 미리 선택받기
            if reply == QMessageBox.Yes:
                selected_dir = QFileDialog.getExistingDirectory(self, "운영일지 저장 폴더 선택 (DB 저장 후 자동 출력)", "")
                if not selected_dir:
                    # 폴더 선택을 취소한 경우 프로세스 보호를 위해 전체 중단
                    QMessageBox.warning(self, "작업 취소", "폴더가 선택되지 않아 DB 저장 및 엑셀 출력 작업이 취소되었습니다.")
                    return

            try:
                # 3. DB 저장 선행 처리
                db_manager.save_manual_meter_data(save_date, final_data)
                success_msg = f"[{save_date}] 일자의 데이터가 DB에 안전하게 반영되었습니다."
                
                # 4. 사용자가 함께 출력을 요청했고, 디렉토리가 정상 지정되었을 경우 엑셀 출력 작동
                if reply == QMessageBox.Yes and selected_dir:
                    excel_report.generate_excel_report(save_date, target_dir=selected_dir)
                    saved_path = os.path.join(selected_dir, f"{save_date}_전기실_운영일지.xlsx")
                    success_msg += f"\n\n이어서 엑셀 운영일지 출력이 완료되었습니다.\n저장 경로:\n{saved_path}"
                
                QMessageBox.information(self, "작업 완료", success_msg)
                
                # 메인 화면 테이블 리프레시 가동
                self.load_data()
                self.update_graph()
                    
            except Exception as e:
                QMessageBox.critical(self, "프로세스 오류", f"데이터 처리 중 오류가 발생했습니다:\n{e}")
    '''

