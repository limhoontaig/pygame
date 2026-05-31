# material_usage_ui.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QFont

class UsageTabUI:
    def setup_ui(self, widget):
        main_layout = QHBoxLayout(widget)
        
        # =================================================================
        # 1. 좌측 영역: 자재 사용 입력 및 수정 폼
        # =================================================================
        left_layout = QVBoxLayout()
        
        self.group_box_use = QGroupBox("자재 사용(출고) 입력")
        grid_use = QGridLayout()
        self.group_box_use.setLayout(grid_use)
        
        notice_font = QFont()
        notice_font.setPointSize(9)
        notice_font.setItalic(True)
        
        # (1) 사용 일자
        grid_use.addWidget(QLabel("사용일자:"), 0, 0)
        self.dateEditUse = QDateEdit()
        self.dateEditUse.setCalendarPopup(True)
        self.dateEditUse.setDate(QDate.currentDate())
        grid_use.addWidget(self.dateEditUse, 0, 1)
        
        # (2) 구분 (세대 / 공용)
        grid_use.addWidget(QLabel("구분:"), 1, 0)
        self.comboType = QComboBox()
        self.comboType.addItems(["공용", "세대"])
        grid_use.addWidget(self.comboType, 1, 1)
        
        # (3) 동 / 호
        grid_use.addWidget(QLabel("동:"), 2, 0)
        self.comboDong = QComboBox()
        grid_use.addWidget(self.comboDong, 2, 1)
        
        grid_use.addWidget(QLabel("호:"), 3, 0)
        self.comboHo = QComboBox()
        grid_use.addWidget(self.comboHo, 3, 1)
        
        # (4) 공종 (Discipline)
        grid_use.addWidget(QLabel("공종:"), 4, 0)
        self.comboDiscipline = QComboBox()
        grid_use.addWidget(self.comboDiscipline, 4, 1)
        
        # (5) 품명 (CB_Item)
        grid_use.addWidget(QLabel("품명:"), 5, 0)
        self.CB_Item = QComboBox()
        grid_use.addWidget(self.CB_Item, 5, 1)
        
        # (6) 규격 (CB_Spec)
        grid_use.addWidget(QLabel("규격:"), 6, 0)
        self.CB_Spec = QComboBox()
        grid_use.addWidget(self.CB_Spec, 6, 1)
        
        # 안내 노티스
        self.lbl_usage_notice = QLabel("💡 공종을 선택하면 해당 공종의 품명만 필터링되며,\n    품명을 선택하면 사용 가능한 규격이 나타납니다.")
        self.lbl_usage_notice.setFont(notice_font)
        self.lbl_usage_notice.setStyleSheet("color: #1976D2; margin-top: 2px; margin-bottom: 5px;")
        grid_use.addWidget(self.lbl_usage_notice, 7, 0, 1, 2)
        
        # (7) 현재 재고 현황 표시창
        grid_use.addWidget(QLabel("현재 재고:"), 8, 0)
        self.LE_CurrentStock = QLineEdit()
        self.LE_CurrentStock.setReadOnly(True)  
        self.LE_CurrentStock.setStyleSheet("background-color: #ECEFF1; color: #37474F; font-weight: bold;")
        self.LE_CurrentStock.setPlaceholderText("품명/규격 선택 시 자동 계산")
        grid_use.addWidget(self.LE_CurrentStock, 8, 1)
        
        # (8) 사용 수량
        grid_use.addWidget(QLabel("사용수량:"), 9, 0)
        self.lineEditUseQty = QLineEdit()
        grid_use.addWidget(self.lineEditUseQty, 9, 1)
        
        # (9) 비고
        grid_use.addWidget(QLabel("비고:"), 10, 0)
        self.lineEditUseRemarks = QLineEdit()
        grid_use.addWidget(self.lineEditUseRemarks, 10, 1)
        
        # (10) 버튼 처리 영역
        button_layout = QHBoxLayout()
        self.btn_save_use = QPushButton("사용 내역 등록")
        self.btn_save_use.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 35px;")
        button_layout.addWidget(self.btn_save_use)
        
        self.btn_cancel_use_edit = QPushButton("수정 취소")
        self.btn_cancel_use_edit.setStyleSheet("background-color: #757575; color: white; font-weight: bold; height: 35px;")
        self.btn_cancel_use_edit.setVisible(False)
        button_layout.addWidget(self.btn_cancel_use_edit)
        
        grid_use.addLayout(button_layout, 11, 0, 1, 2)
        
        left_layout.addWidget(self.group_box_use)
        left_layout.addStretch()
        
        # =================================================================
        # 2. 우측 영역: 사용 대장 테이블 및 제어 버튼
        # =================================================================
        right_layout = QVBoxLayout()
        
        top_bar = QHBoxLayout()
        self.btn_edit_use_row = QPushButton("선택 내역 수정")
        self.btn_edit_use_row.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 6px 12px;")
        top_bar.addWidget(self.btn_edit_use_row)
        
        self.btn_delete_use_row = QPushButton("선택 내역 삭제")
        self.btn_delete_use_row.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px 12px;")
        top_bar.addWidget(self.btn_delete_use_row)
        
        top_bar.addStretch()
        right_layout.addLayout(top_bar)
        
        self.tableWidgetUse = QTableWidget()
        self.tableWidgetUse.setColumnCount(10)
        self.tableWidgetUse.setHorizontalHeaderLabels([
            "사용일자", "구분", "동", "호", "공종", "품명", "규격", "수량", "비고", "입력자"
        ])
        self.tableWidgetUse.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidgetUse.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.tableWidgetUse)
        
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)