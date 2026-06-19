# material_usage_ui.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate, Qt
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
        
        # (3) 동 선택
        grid_use.addWidget(QLabel("동 선택:"), 2, 0)
        self.comboDong = QComboBox()
        self.comboDong.setEditable(True)
        grid_use.addWidget(self.comboDong, 2, 1)
        
        # (4) 호 선택 및 층 복도 체크박스 영역
        grid_use.addWidget(QLabel("호 선택:"), 3, 0)
        ho_layout = QHBoxLayout()
        self.comboHo = QComboBox()
        self.comboHo.setEditable(True)
        ho_layout.addWidget(self.comboHo, 1)
        
        self.chkFloorCorridor = QCheckBox("층 복도")
        self.lblFloorStatus = QLabel("")
        self.lblFloorStatus.setStyleSheet("color: #E65100; font-weight: bold; font-size: 11px;")
        
        ho_layout.addWidget(self.chkFloorCorridor)
        ho_layout.addWidget(self.lblFloorStatus)
        grid_use.addLayout(ho_layout, 3, 1)
        
        # (5) 공종
        grid_use.addWidget(QLabel("공종:"), 4, 0)
        self.comboDiscipline = QComboBox()
        self.comboDiscipline.setEditable(True)
        grid_use.addWidget(self.comboDiscipline, 4, 1)
        
        # (6) 품명
        grid_use.addWidget(QLabel("품명:"), 5, 0)
        self.comboItemName = QComboBox()
        self.comboItemName.setEditable(True)
        grid_use.addWidget(self.comboItemName, 5, 1)
        
        # (7) 규격
        grid_use.addWidget(QLabel("규격:"), 6, 0)
        self.comboSpec = QComboBox()
        self.comboSpec.setEditable(True)
        grid_use.addWidget(self.comboSpec, 6, 1)
        
        # (8) 수량
        grid_use.addWidget(QLabel("출고수량:"), 7, 0)
        self.lineEditQty = QLineEdit()
        grid_use.addWidget(self.lineEditQty, 7, 1)
        
        # (9) 비고
        grid_use.addWidget(QLabel("비고(상세위치):"), 8, 0)
        self.lineEditRemarks = QLineEdit()
        grid_use.addWidget(self.lineEditRemarks, 8, 1)

        # (10) 현장 자재 사용 사진 등록 UI 영역 (3장)
        grid_use.addWidget(QLabel("현장 사진:"), 9, 0)
        photo_main_layout = QVBoxLayout()
        self.photo_widgets = []
        for i in range(3):
            p_layout = QHBoxLayout()
            lbl_status = QLabel(f"사진 {i+1}: 등록되지 않음")
            lbl_status.setStyleSheet("color: gray;")
            
            btn_add = QPushButton("등록")
            btn_add.setFixedWidth(50)
            
            btn_del = QPushButton("X")
            btn_del.setFixedWidth(25)
            btn_del.setStyleSheet("background-color: #757575; color: white; font-weight: bold;")
            
            p_layout.addWidget(lbl_status, 1)
            p_layout.addWidget(btn_add)
            p_layout.addWidget(btn_del)
            photo_main_layout.addLayout(p_layout)
            self.photo_widgets.append({"label": lbl_status, "btn_add": btn_add, "btn_del": btn_del})
        grid_use.addLayout(photo_main_layout, 9, 1)
        
        # 제어 버튼 영역
        button_layout = QHBoxLayout()
        self.btn_save_use = QPushButton("자재 출고 등록")
        self.btn_save_use.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; height: 35px;")
        button_layout.addWidget(self.btn_save_use)
        
        self.btn_cancel_use_edit = QPushButton("수정 취소")
        self.btn_cancel_use_edit.setStyleSheet("background-color: #757575; color: white; font-weight: bold; height: 35px;")
        self.btn_cancel_use_edit.setVisible(False)
        button_layout.addWidget(self.btn_cancel_use_edit)
        grid_use.addLayout(button_layout, 10, 0, 1, 2)
        
        left_layout.addWidget(self.group_box_use)
        left_layout.addStretch()
        
        # =================================================================
        # 2. 우측 영역: 사용 대장 테이블 및 🌟하단 사진 미리보기 액자
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
        self.tableWidgetUse.setColumnCount(13) 
        self.tableWidgetUse.setHorizontalHeaderLabels([
            "사용일자", "구분", "동", "호", "공종", "품명", "규격", "수량", "비고", "사진1", "사진2", "사진3", "입력자"
        ])
        self.tableWidgetUse.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidgetUse.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.tableWidgetUse)
        
        # 🌟 [신규 추가] 테이블 하단 선택 행 사진 실시간 미리보기 틀 구성
        self.preview_group = QGroupBox("선택 내역 현장 사진 미리보기")
        preview_layout = QHBoxLayout(self.preview_group)
        self.preview_group.setFixedHeight(190)
        
        self.lbl_previews = []
        for i in range(3):
            lbl_img = QLabel(f"사진 {i+1} 없음")
            lbl_img.setAlignment(Qt.AlignCenter)
            lbl_img.setStyleSheet("border: 1px dashed #BDBDBD; background-color: #FAFAFA; color: #9E9E9E; font-size: 11px;")
            lbl_img.setFixedSize(220, 150)
            preview_layout.addWidget(lbl_img)
            self.lbl_previews.append(lbl_img)
            
        preview_layout.addStretch()
        right_layout.addWidget(self.preview_group)
        
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)