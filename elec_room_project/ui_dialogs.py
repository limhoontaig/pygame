# ui_dialogs.py
import sqlite3
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QGroupBox, QFormLayout, QLineEdit, QGridLayout, QDialogButtonBox, QMessageBox, QComboBox
from PyQt5.QtCore import QDate, Qt

import db_manager # DB 조회를 위해 가져옴

class ManualMeterInputDialog(QDialog):
    """독립된 3개 계량장치의 11개 지침을 날짜별로 통합 입력/수정하는 팝업 창"""
    def __init__(self, default_date_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("독립 계량장치 일일 지침 수동 입력/수정")
        self.resize(700, 500) # 그룹화로 인해 UI 보기 좋게 사이즈를 약간 키웠습니다.

        # [여기 추가] 다이얼로그 전체 폰트 설정 (기존 폰트에서 크기 +1, 볼드 처리)
        current_font = self.font()                   # 현재 기본 폰트 가져오기
        current_font.setPointSize(current_font.pointSize() + 1) # 크기 1 사이즈 증가
        current_font.setBold(True)                   # 볼드체(굵게) 설정
        self.setFont(current_font)                   # 다이얼로그 전체에 적용 (자식들에게 상속됨)
        
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
        
        # 전체 그룹을 2x2로 배치할 메인 그리드 레이아웃
        grid_layout = QGridLayout()
        self.inputs = {}
        
        # --- [0, 0] 메인 계량기 그룹 ---
        main_group = QGroupBox("메인 계량장치")
        main_form = QFormLayout()
        main_fields = [
            ('main_active', '메인 유효 (kWh)'),
            ('main_reactive', '메인 무효 (kVarh)')
        ]
        for field, label in main_fields:
            edit = QLineEdit()
            main_form.addRow(label, edit)
            self.inputs[field] = edit
        main_group.setLayout(main_form)
        grid_layout.addWidget(main_group, 0, 0)
        
        # --- [0, 1] 산업용 그룹 ---
        ind_group = QGroupBox("산업용 전력")
        ind_form = QFormLayout()
        ind_fields = [
            ('ind_mid', '중간부하'),
            ('ind_max', '최대부하'),
            ('ind_light', '경부하')
        ]
        for field, label in ind_fields:
            edit = QLineEdit()
            ind_form.addRow(label, edit)
            self.inputs[field] = edit
        ind_group.setLayout(ind_form)
        grid_layout.addWidget(ind_group, 0, 1)
        
        # --- [1, 0] 가로등 그룹 ---
        street_group = QGroupBox("가로등 전력")
        street_form = QFormLayout()
        street_fields = [
            ('street_mid', '중간부하'),
            ('street_max', '최대부하'),
            ('street_light', '경부하')
        ]
        for field, label in street_fields:
            edit = QLineEdit()
            street_form.addRow(label, edit)
            self.inputs[field] = edit
        street_group.setLayout(street_form)
        grid_layout.addWidget(street_group, 1, 0)
        
        # --- [1, 1] 지열 그룹 ---
        geo_group = QGroupBox("지열 시스템")
        geo_form = QFormLayout()
        geo_fields = [
            ('geo_1', '지열 1호기'),
            ('geo_2', '지열 2호기'),
            ('geo_3', '지열 3호기')
        ]
        for field, label in geo_fields:
            edit = QLineEdit()
            geo_form.addRow(label, edit)
            self.inputs[field] = edit
        geo_group.setLayout(geo_form)
        grid_layout.addWidget(geo_group, 1, 1)
        
        # 메인 레이아웃에 그리드 추가
        main_layout.addLayout(grid_layout)
        
        # 3. 저장 및 취소 버튼 영역
        buttons = QDialogButtonBox()
        self.save_button = buttons.addButton(QDialogButtonBox.Save)
        self.cancel_button = buttons.addButton(QDialogButtonBox.Cancel)
        
        self.save_button.clicked.connect(self.validate_and_accept)
        self.cancel_button.clicked.connect(self.reject)
        
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

class FieldInspectionDialog(QDialog):
    """현장 점검 근무자 입력 및 차수 선택 팝업 창"""
    def __init__(self, default_date_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("현장 일일 점검 기록 입력")
        self.resize(400, 250)

        # 기존 스타일과 통일성 유지 (글씨 굵게, 크기 +1)
        current_font = self.font()
        current_font.setPointSize(current_font.pointSize() + 1)
        current_font.setBold(True)
        self.setFont(current_font)

        layout = QVBoxLayout(self)

        # 1. 날짜 설정 (메인 화면에서 선택된 날짜 자동 고정)
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("점검 일자:"))
        self.date_edit = QDateEdit(QDate.fromString(default_date_str, "yyyy-MM-dd"))
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setEnabled(False)  # 임의 날짜 조작 방지를 위해 읽기 전용 처리 가능
        date_layout.addWidget(self.date_edit)
        layout.addLayout(date_layout)

        # 2. 점검 차수 선택 (콤보박스)
        round_layout = QHBoxLayout()
        round_layout.addWidget(QLabel("점검 차수:"))
        self.combo_round = QComboBox()
        self.combo_round.addItems(["1차 점검", "2차 점검", "3차 점검"])
        round_layout.addWidget(self.combo_round)
        layout.addLayout(round_layout)

        # 3. 점검자 이름 입력
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("점검자 성명:"))
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("성명을 입력하세요")
        name_layout.addWidget(self.input_name)
        layout.addLayout(name_layout)

        # 4. 하단 버튼 (확인 / 취소)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def validate_and_accept(self):
        if not self.input_name.text().strip():
            QMessageBox.warning(self, "입력 오류", "점검자 성명을 정확히 입력해 주세요.")
            self.input_name.setFocus()
            return
        self.accept()