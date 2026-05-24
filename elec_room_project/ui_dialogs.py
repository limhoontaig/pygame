# ui_dialogs.py
import sqlite3
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QGroupBox, QFormLayout, QLineEdit, QGridLayout, QDialogButtonBox, QMessageBox
from PyQt5.QtCore import QDate, Qt

import db_manager # DB 조회를 위해 가져옴

'''
class ManualMeterInputDialog(QDialog):
    """독립된 3개 계량장치의 11개 지침을 날짜별로 통합 입력/수정하는 팝업 창"""
    def __init__(self, default_date_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("독립 계량장치 일일 지침 수동 입력/수정")
        self.resize(650, 450)
        
        main_layout = QVBoxLayout()
        
        # 1. 날짜 선택 영역
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("<b>검침 대상 일자:</b>"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.fromString(default_date_str, "yyyy-MM-dd"))
        
        # 💡 [여기서 크기 및 스타일을 확장합니다]
        self.date_edit.setMinimumWidth(120) # 가로 최소 크기를 150 픽셀로 강제 확장 (기존보다 훨씬 넓어집니다)
        self.date_edit.setAlignment(Qt.AlignCenter) # 날짜 글자를 가운데 정렬하여 가독성 향상
        self.date_edit.setStyleSheet("font-size: 13px; padding: 3px;") # 글자 크기 및 내부 여백 조정

        self.date_edit.dateChanged.connect(self.load_date_data) # 날짜 바꾸면 즉시 기존 데이터 로드
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        main_layout.addLayout(date_layout)
        
        # 2. 3대 장치 입력 폼 구성 (입력 필드 딕셔너리 정렬)
        self.inputs = {}
        grid = QGridLayout()
        
        # [그룹 1] 한전 메인 데이터
        group_main = QGroupBox("한전 메인 계량기")
        layout_main = QFormLayout()
        self.inputs["main_active"] = QLineEdit()
        self.inputs["main_reactive"] = QLineEdit()
        layout_main.addRow("메인 유효 전력량 (4번):", self.inputs["main_active"])
        layout_main.addRow("메인 무효 전력량 (5번):", self.inputs["main_reactive"])
        group_main.setLayout(layout_main)
        grid.addWidget(group_main, 0, 0)
        
        # [그룹 2] 산업용 전력 데이터
        group_ind = QGroupBox("산업용 (급수/정화조)")
        layout_ind = QFormLayout()
        self.inputs["ind_mid"] = QLineEdit()
        self.inputs["ind_max"] = QLineEdit()
        self.inputs["ind_light"] = QLineEdit()
        layout_ind.addRow("산업용 유효 중간 (13번):", self.inputs["ind_mid"])
        layout_ind.addRow("산업용 유효 최대 (14번):", self.inputs["ind_max"])
        layout_ind.addRow("산업용 유효 경부하 (15번):", self.inputs["ind_light"])
        group_ind.setLayout(layout_ind)
        grid.addWidget(group_ind, 0, 1)
        
        # [그룹 3] 가로등 전력 데이터
        group_street = QGroupBox("가로등 (LV10)")
        layout_street = QFormLayout()
        self.inputs["street_mid"] = QLineEdit()
        self.inputs["street_max"] = QLineEdit()
        self.inputs["street_light"] = QLineEdit()
        layout_street.addRow("가로등 유효 중간 (13번):", self.inputs["street_mid"])
        layout_street.addRow("가로등 유효 최대 (14번):", self.inputs["street_max"])
        layout_street.addRow("가로등 유효 경부하 (15번):", self.inputs["street_light"])
        group_street.setLayout(layout_street)
        grid.addWidget(group_street, 1, 0)
        
        # [그룹 4] 지열 시스템 데이터
        group_geo = QGroupBox("지열 시스템 지침")
        layout_geo = QFormLayout()
        self.inputs["geo_1"] = QLineEdit()
        self.inputs["geo_2"] = QLineEdit()
        self.inputs["geo_3"] = QLineEdit()
        layout_geo.addRow("지열 1호기 지침:", self.inputs["geo_1"])
        layout_geo.addRow("지열 2호기 지침:", self.inputs["geo_2"])
        layout_geo.addRow("지열 3호기 지침:", self.inputs["geo_3"])
        group_geo.setLayout(layout_geo)
        grid.addWidget(group_geo, 1, 1)
        
        main_layout.addLayout(grid)
      
        # 안내 문구
        lbl_info = QLabel("※ 숫자를 입력하면 실시간 저장/수정되며, 공백으로 두면 빈 데이터로 처리됩니다.")
        lbl_info.setStyleSheet("color: blue; font-size: 11px;")
        main_layout.addWidget(lbl_info)
        
        # 3. 저장 및 취소 버튼
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # 에러가 발생하여 변경함
        # buttons.accepted.connect(self.validate_and_accept)
        # buttons.rejected.connect(self.reject)
        # ⭕ 변경: 버튼 클릭 시 직접 시그널을 연결하지 않고, 버튼 객체를 찾아 개별 클릭 이벤트로 매핑합니다.
        buttons.button(QDialogButtonBox.Save).clicked.connect(self.validate_and_accept)
        buttons.button(QDialogButtonBox.Cancel).clicked.connect(self.close_dialog) # 커스텀 종료 함수로 연결
        main_layout.addWidget(buttons)
        
        self.setLayout(main_layout)
        
        # 최초 실행 시 현재 설정된 날짜 데이터 로딩 가동
        self.load_date_data()

'''
class ManualMeterInputDialog(QDialog):
    """독립된 3개 계량장치의 11개 지침을 날짜별로 통합 입력/수정하는 팝업 창"""
    def __init__(self, default_date_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("독립 계량장치 일일 지침 수동 입력/수정")
        self.resize(650, 450)
        
        main_layout = QVBoxLayout()
        
        # 1. 날짜 선택 영역
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("<b>검침 대상 일자:</b>"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.fromString(default_date_str, "yyyy-MM-dd"))
        self.date_edit.setMinimumWidth(120)
        
        # 날짜 변경 시 데이터를 새로 로드하는 이벤트 연결
        self.date_edit.dateChanged.connect(self.load_date_data)
        
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        main_layout.addLayout(date_layout)
        
        # 2. 입력 필드 그룹 생성 (그리드 레이아웃)
        grid_layout = QGridLayout()
        self.inputs = {}
        
        # 필드 정의 (db_manager.METER_FIELDS 와 일치)
        fields = [
            ('main_active', '메인 유효 (kWh)'),
            ('main_reactive', '메인 무효 (kVarh)'),
            ('ind_mid', '산업용 중간부하'),
            ('ind_max', '산업용 최대부하'),
            ('ind_light', '산업용 경부하'),
            ('street_mid', '가로등 중간부하'),
            ('street_max', '가로등 최대부하'),
            ('street_light', '가로등 경부하'),
            ('geo_1', '지열 1호기'),
            ('geo_2', '지열 2호기'),
            ('geo_3', '지열 3호기')
        ]
        
        for idx, (field_name, label_text) in enumerate(fields):
            row = idx // 2
            col = (idx % 2) * 2
            
            lbl = QLabel(label_text)
            edit = QLineEdit()
            
            grid_layout.addWidget(lbl, row, col)
            grid_layout.addWidget(edit, row, col + 1)
            
            self.inputs[field_name] = edit
            
        main_layout.addLayout(grid_layout)
        
        # 3. 저장 및 취소 버튼 영역 (💡 크래시를 방지하는 가장 안전한 연결 방식)
        buttons = QDialogButtonBox()
        self.save_button = buttons.addButton(QDialogButtonBox.Save)
        self.cancel_button = buttons.addButton(QDialogButtonBox.Cancel)
        
        # PyQt 내부 시그널 기능 대신 커스텀 함수로 직접 바인딩
        self.save_button.clicked.connect(self.validate_and_accept)
        self.cancel_button.clicked.connect(self.reject)  # 부모 QDialog의 reject 호출
        
        main_layout.addWidget(buttons)
        self.setLayout(main_layout)
        
        # 최초 실행 시 데이터 로드
        self.load_date_data()


    def load_date_data(self):
        """날짜가 변경될 때마다 DB를 뒤져 해당 일자의 기존 수치를 양식에 표기합니다."""
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        # db_manager의 조회 함수 호출
        current_data = db_manager.get_manual_meter_data(date_str)
        
        for field, value in current_data.items():
            if field in self.inputs: # 딕셔너리에 필드가 존재할 때만 입력창에 값 세팅   
                self.inputs[field].setText(value)
            
    def validate_and_accept(self):
        """입력된 값들이 정상적인 숫자 포맷인지 최종 무결성 검사를 수행합니다."""
        for field, edit in self.inputs.items():
            text = edit.text().strip()
            if text:
                try:
                    float(text)
                except ValueError:
                    QMessageBox.warning(self, "포맷 오류", "지침 입력 값은 순수 숫자(또는 소수점)만 입력 가능합니다.")
                    edit.setFocus()
                    return  # 검증 실패 시 창을 닫지 않고 함수 종료
                    
        # 모든 검증을 통과하면 부모 창(Main Window)으로 Accepted 신호 전송
        self.accept()
    def close_dialog(self):
        """Cancel 버튼 클릭 시 안전하게 창을 닫습니다."""
        self.done(QDialog.Rejected) # QDialog를 거치지 않고 직접 명시적으로 거절(Rejected) 코드로 종료

    def get_final_inputs(self):
        """저장 승인 시 가공된 날짜 및 11개 필드 딕셔너리를 메인 윈도우로 반환합니다."""
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        data_dict = {field: edit.text().strip() for field, edit in self.inputs.items()}
        return date_str, data_dict
