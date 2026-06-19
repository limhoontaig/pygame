# material_inbound_tab.py
import os
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QDate

# 분리한 UI 파일과 기능 로직 파일을 임포트합니다.
from inbound_ui import InboundUI
from inbound_presenter import InboundPresenter

class InboundTab(QWidget):
    def __init__(self, user_name="미인증"):
        super().__init__()
        self.current_user = user_name
        
        # 상태 제어 플래그 변수 정의
        self.is_edit_mode = False
        self.editing_row_id = None  
        self.is_calculating = False  
        self.selected_photos = [None, None, None]

        # 디렉토리 설정
        self.image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inbound_images")
        if not os.path.exists(self.image_dir): os.makedirs(self.image_dir)

        # 1. 쪼개놓은 UI 모듈 로드 및 빌드
        self.ui_manager = InboundUI()
        self.ui_manager.setup_ui(self)
        
        # 2. 쪼개놓은 기능 로직 엔진(Presenter) 로드
        self.presenter = InboundPresenter(self)
        
        # 3. 신호 결합 및 초기화 명령
        self.bind_signals()
        self.refresh_all_combos()
        self.table_display_in()

    def bind_signals(self):
        """디자인 컴포넌트와 기능 처리 엔진을 연결(바인딩)합니다."""
        # 버튼 매핑
        self.btn_save_in.clicked.connect(self.presenter.process_inbound_save)
        self.btn_cancel_edit.clicked.connect(self.clear_input_fields)
        self.btn_edit_row.clicked.connect(self.presenter.load_selected_row_to_form)
        self.btn_delete_in.clicked.connect(self.presenter.delete_selected_row)
        self.btn_export_excel.clicked.connect(self.presenter.export_to_excel)

        # 실시간 자동 계산 바인딩
        self.lineEditInQty.textChanged.connect(self.presenter.calculate_from_price)
        self.lineEditInPrice.textChanged.connect(self.presenter.calculate_from_price)
        self.lineEditInTotalPrice.textChanged.connect(self.presenter.calculate_from_total_price)

        # 계층형 필터링 바인딩
        self.comboBoxInDiscipline.currentTextChanged.connect(self.presenter.filter_name_combo)
        self.comboBoxInName.currentTextChanged.connect(self.presenter.filter_spec_combo)
        
        # 테이블 선택 프리뷰 매핑
        self.tableWidgetInIn.cellClicked.connect(self.presenter.show_photo_preview_from_table)

    # 뷰와 프레젠터 간 교차 제어를 위한 중간 가교 함수들
    def refresh_all_combos(self): self.presenter.refresh_all_combos()
    def table_display_in(self): self.presenter.table_display_in()
    def filter_name_combo(self, txt): self.presenter.filter_name_combo(txt)
    def filter_spec_combo(self, txt): self.presenter.filter_spec_combo(txt)

    def clear_input_fields(self):
        """서식 입력창 컴포넌트들을 깨끗이 초기화합니다."""
        self.is_edit_mode = False; self.editing_row_id = None
        self.dateEditIn.setDate(QDate.currentDate())
        self.comboBoxInDiscipline.clearEditText(); self.comboBoxInName.clearEditText(); self.comboBoxInSpec.clearEditText()
        
        self.is_calculating = True
        self.lineEditInQty.clear(); self.lineEditInPrice.clear(); self.lineEditInTotalPrice.clear()
        self.is_calculating = False
        self.lineEditInSupplier.clear(); self.lineEditInRemarks.clear()

        self.selected_photos = [None, None, None]
        for i in range(3):
            self.photo_widgets[i]["label"].setText(f"사진 {i+1}: 등록되지 않음"); self.photo_widgets[i]["label"].setStyleSheet("color: gray;")
            self.lbl_previews[i].clear(); self.lbl_previews[i].setText(f"사진 {i+1} 없음")
            self.lbl_previews[i].setStyleSheet("border: 1px dashed #BDBDBD; background-color: #FAFAFA; color: #9E9E9E; font-size: 11px;")
        
        self.group_box_in.setTitle("자재 입고(등록) 입력")
        self.btn_save_in.setText("입고 내역 등록")
        self.btn_save_in.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 35px;")
        self.btn_cancel_edit.setVisible(False)