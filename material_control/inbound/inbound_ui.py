# inbound_ui.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont

class InboundUI:
    def setup_ui(self, widget):
        """widget(QWidget) 객체 위에 입고 탭 화면 구조를 생성합니다."""
        main_layout = QHBoxLayout(widget)
        notice_font = QFont()
        notice_font.setPointSize(9)
        notice_font.setItalic(True)
        
        # -------------------------------------------------------------
        # 좌측 영역: 입력 폼 그룹박스
        # -------------------------------------------------------------
        left_layout = QVBoxLayout()
        widget.group_box_in = QGroupBox("자재 입고(등록) 입력")
        grid_in = QGridLayout()
        widget.group_box_in.setLayout(grid_in)
        
        grid_in.addWidget(QLabel("입고일자:"), 0, 0)
        widget.dateEditIn = QDateEdit()
        widget.dateEditIn.setCalendarPopup(True)
        widget.dateEditIn.setDate(QDate.currentDate())
        grid_in.addWidget(widget.dateEditIn, 0, 1)
        
        grid_in.addWidget(QLabel("공종:"), 1, 0)
        widget.comboBoxInDiscipline = QComboBox()  
        widget.comboBoxInDiscipline.setEditable(True)
        widget.comboBoxInDiscipline.setPlaceholderText("공종 입력 또는 선택")
        grid_in.addWidget(widget.comboBoxInDiscipline, 1, 1)

        grid_in.addWidget(QLabel("품명:"), 2, 0)
        widget.comboBoxInName = QComboBox()        
        widget.comboBoxInName.setEditable(True)
        widget.comboBoxInName.setPlaceholderText("품명 입력 또는 선택")
        grid_in.addWidget(widget.comboBoxInName, 2, 1)
        
        grid_in.addWidget(QLabel("규격:"), 3, 0)
        widget.comboBoxInSpec = QComboBox()
        widget.comboBoxInSpec.setEditable(True)
        widget.comboBoxInSpec.setPlaceholderText("신규 추가 품목")
        grid_in.addWidget(widget.comboBoxInSpec, 3, 1)
        
        widget.lbl_combo_notice = QLabel("※ 리스트에 없는 신규 품종은 직접 타이핑하여 입력하시면 됩니다.")
        widget.lbl_combo_notice.setFont(notice_font)
        widget.lbl_combo_notice.setStyleSheet("color: #1976D2; margin-top: 2px; margin-bottom: 8px;")
        grid_in.addWidget(widget.lbl_combo_notice, 4, 0, 1, 2)
        
        grid_in.addWidget(QLabel("입고수량:"), 5, 0)
        widget.lineEditInQty = QLineEdit()
        grid_in.addWidget(widget.lineEditInQty, 5, 1)
        
        grid_in.addWidget(QLabel("단가:"), 6, 0)
        widget.lineEditInPrice = QLineEdit()
        grid_in.addWidget(widget.lineEditInPrice, 6, 1)
        
        widget.lbl_price_notice = QLabel("💡 단가 또는 총금액 중 하나만 입력해도 자동 역산됩니다.")
        widget.lbl_price_notice.setFont(notice_font)
        widget.lbl_price_notice.setStyleSheet("color: #2E7D32; margin-top: 4px; margin-bottom: 4px;")
        grid_in.addWidget(widget.lbl_price_notice, 7, 0, 1, 2)
        
        grid_in.addWidget(QLabel("총금액:"), 8, 0)
        widget.lineEditInTotalPrice = QLineEdit()
        grid_in.addWidget(widget.lineEditInTotalPrice, 8, 1)

        grid_in.addWidget(QLabel("공급처:"), 9, 0)
        widget.lineEditInSupplier = QLineEdit()
        grid_in.addWidget(widget.lineEditInSupplier, 9, 1)
        
        grid_in.addWidget(QLabel("비고:"), 10, 0)
        widget.lineEditInRemarks = QLineEdit()
        grid_in.addWidget(widget.lineEditInRemarks, 10, 1)

        # 사진 첨부 인터페이스 (버튼 및 레이블)
        grid_in.addWidget(QLabel("현장 사진:"), 11, 0)
        photo_main_layout = QVBoxLayout()
        widget.photo_widgets = []
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
            widget.photo_widgets.append({"label": lbl_status, "btn_add": btn_add, "btn_del": btn_del})
        grid_in.addLayout(photo_main_layout, 11, 1)
        
        button_layout = QHBoxLayout()
        widget.btn_save_in = QPushButton("입고 내역 등록")
        widget.btn_save_in.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 35px;")
        button_layout.addWidget(widget.btn_save_in)
        
        widget.btn_cancel_edit = QPushButton("수정 취소")
        widget.btn_cancel_edit.setStyleSheet("background-color: #757575; color: white; font-weight: bold; height: 35px;")
        widget.btn_cancel_edit.setVisible(False)
        button_layout.addWidget(widget.btn_cancel_edit)
        grid_in.addLayout(button_layout, 12, 0, 1, 2)
        
        left_layout.addWidget(widget.group_box_in)
        left_layout.addStretch()
        
        # -------------------------------------------------------------
        # 우측 영역: 데이터 테이블 및 하단 액자 미리보기
        # -------------------------------------------------------------
        right_layout = QVBoxLayout()
        
        top_bar = QHBoxLayout()
        widget.btn_edit_row = QPushButton("선택 내역 수정")
        widget.btn_edit_row.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 6px 12px;")
        top_bar.addWidget(widget.btn_edit_row)
        
        widget.btn_delete_in = QPushButton("선택 내역 삭제")
        widget.btn_delete_in.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px 12px;")
        top_bar.addWidget(widget.btn_delete_in)

        # 🌟 [신규 추가] 기간 설정 UI 컴포넌트들 수평 배치
        top_bar.addWidget(QLabel(" |  기간:"))
        widget.dateEditStart = QDateEdit()
        widget.dateEditStart.setCalendarPopup(True)
        widget.dateEditStart.setDate(QDate.currentDate().addMonths(-1)) # 기본값: 한 달 전
        widget.dateEditStart.setFixedWidth(105)
        top_bar.addWidget(widget.dateEditStart)
        
        top_bar.addWidget(QLabel("~"))
        
        widget.dateEditEnd = QDateEdit()
        widget.dateEditEnd.setCalendarPopup(True)
        widget.dateEditEnd.setDate(QDate.currentDate())                 # 기본값: 오늘 날짜
        widget.dateEditEnd.setFixedWidth(105)
        top_bar.addWidget(widget.dateEditEnd)
        
        widget.btn_search_range = QPushButton("기간조회")
        widget.btn_search_range.setStyleSheet("background-color: #0288D1; color: white; font-weight: bold; padding: 6px 10px;")
        top_bar.addWidget(widget.btn_search_range)
        
        widget.btn_search_month = QPushButton("월간보고")
        widget.btn_search_month.setStyleSheet("background-color: #673AB7; color: white; font-weight: bold; padding: 6px 10px;")
        top_bar.addWidget(widget.btn_search_month)
        
        widget.btn_search_clear = QPushButton("전체해제")
        widget.btn_search_clear.setStyleSheet("background-color: #607D8B; color: white; padding: 6px 8px;")
        top_bar.addWidget(widget.btn_search_clear)

        widget.btn_export_excel = QPushButton("엑셀 내보내기 (Report)")
        widget.btn_export_excel.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold; padding: 6px 12px;")
        top_bar.addWidget(widget.btn_export_excel)
        top_bar.addStretch()
        right_layout.addLayout(top_bar)
        
        widget.tableWidgetInIn = QTableWidget()
        widget.tableWidgetInIn.setColumnCount(13) 
        widget.tableWidgetInIn.setHorizontalHeaderLabels([
            "입고일자", "공종", "품명", "규격", "수량", "단가", "총금액", "공급처", "비고", "사진1", "사진2", "사진3", "입력자"
        ])
        widget.tableWidgetInIn.setSelectionBehavior(QAbstractItemView.SelectRows)
        widget.tableWidgetInIn.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(widget.tableWidgetInIn)
        
        # 하단 선택 자재 사진 미리보기 액자
        widget.preview_group = QGroupBox("선택 자재 사진 미리보기")
        preview_layout = QHBoxLayout(widget.preview_group)
        widget.preview_group.setFixedHeight(190)
        
        widget.lbl_previews = []
        for i in range(3):
            lbl_img = QLabel(f"사진 {i+1} 없음")
            lbl_img.setAlignment(Qt.AlignCenter)
            lbl_img.setStyleSheet("border: 1px dashed #BDBDBD; background-color: #FAFAFA; color: #9E9E9E; font-size: 11px;")
            lbl_img.setFixedSize(220, 150)
            preview_layout.addWidget(lbl_img)
            widget.lbl_previews.append(lbl_img)
            
        preview_layout.addStretch()
        right_layout.addWidget(widget.preview_group)
        
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)