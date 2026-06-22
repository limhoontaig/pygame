# material_usage_tab.py
import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor, QPixmap
import common.database as database
from usage.material_usage_ui import UsageTabUI

# 분리된 하위 모듈 가져오기
from usage.usage_data_manager import UsageDataManager
from usage.usage_event_handler import UsageEventHandler
from usage.usage_printer import UsagePrinter

class UsageTab(QWidget):
    def __init__(self, user_name="미인증"):
        super().__init__()
        self.current_user = user_name
        
        self.is_edit_mode = False
        self.editing_row_id = None
        self.is_loading_row = False 
        self.is_syncing_ho_disp = False

        self.image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usage_images")
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)

        self.selected_photos = [None, None, None]

        # 기능별 전담 클래스 인스턴스화
        self.data_manager = UsageDataManager(self)
        self.event_handler = UsageEventHandler(self)
        self.printer = UsagePrinter(self)  # 출력 기능 인스턴스

        # 1. UI 스킨 결합 및 변수 참조 연결
        self.ui = UsageTabUI()
        self.ui.setup_ui(self)
        self.bind_ui_variables()
        self.add_printer_buttons() # 출력 버튼 추가용 확장 메서드

        # 2. 시그널 바인딩 및 데이터 로드
        self.connect_signals()
        self.event_handler.handle_type_change(self.comboType.currentText())
        self.table_display_usage()

    def bind_ui_variables(self):
        self.comboType = self.ui.comboType
        self.comboDong = self.ui.comboDong
        self.comboHo = self.ui.comboHo
        self.chkFloorCorridor = self.ui.chkFloorCorridor 
        self.lblFloorStatus = self.ui.lblFloorStatus     
        self.comboDiscipline = self.ui.comboDiscipline
        self.CB_Item = self.ui.comboItemName
        self.CB_Spec = self.ui.comboSpec
        self.LE_CurrentStock = QLabel() 
        self.lineEditUseQty = self.ui.lineEditQty
        self.lineEditUseRemarks = self.ui.lineEditRemarks
        self.tableWidgetUse = self.ui.tableWidgetUse
        self.group_box_use = self.ui.group_box_use
        self.btn_save_use = self.ui.btn_save_use
        self.btn_cancel_use_edit = self.ui.btn_cancel_use_edit
        self.dateEditUse = self.ui.dateEditUse
        self.photo_widgets = self.ui.photo_widgets
        self.lbl_previews = self.ui.lbl_previews

    def add_printer_buttons(self):
        """출력 관련 버튼을 UI 레이아웃의 상단 바 빈 공간에 동적으로 추가"""
        # UI 파일의 우측 상단 레이아웃 배치 구조 확인 후 연결
        # 팁: self.ui.btn_delete_use_row 옆에 추가하기 위해 조상 레이아웃을 찾음
        top_bar_layout = self.ui.btn_delete_use_row.parentWidget().layout() or self.tableWidgetUse.parentWidget().findChild(QHBoxLayout)
        
        if top_bar_layout:
            self.btn_excel_export = QPushButton("📊 엑셀 대장 출력")
            self.btn_excel_export.setStyleSheet("background-color: #1E7145; color: white; font-weight: bold; padding: 6px 12px;")
            self.btn_excel_export.clicked.connect(self.printer.export_to_excel)
            
            self.btn_print = QPushButton("🖨️ 실물 인쇄")
            self.btn_print.setStyleSheet("background-color: #607D8B; color: white; font-weight: bold; padding: 6px 12px;")
            self.btn_print.clicked.connect(self.printer.print_ledger)
            
            # 레이아웃에 추가 (Stretch 공간 이전에 추가하기 위해 삽입 인덱스 조율 가능)
            top_bar_layout.addWidget(self.btn_excel_export)
            top_bar_layout.addWidget(self.btn_print)

    def connect_signals(self):
        # 이벤트 핸들러 클래스의 메서드로 직접 매핑 및 연결
        self.comboType.currentTextChanged.connect(self.event_handler.handle_type_change)
        self.comboDong.currentTextChanged.connect(self.event_handler.handle_dong_change)
        self.comboHo.currentTextChanged.connect(self.event_handler.handle_ho_change)
        self.comboDiscipline.currentTextChanged.connect(self.event_handler.handle_discipline_change)
        self.CB_Item.currentTextChanged.connect(self.event_handler.handle_item_change)
        self.CB_Spec.currentTextChanged.connect(self.update_stock_display)
        
        self.tableWidgetUse.itemSelectionChanged.connect(self.highlight_selected_row)
        self.tableWidgetUse.cellClicked.connect(self.show_photo_preview_from_table)
        
        # 저장 / 편집 / 삭제 바인딩
        self.btn_save_use.clicked.connect(self.data_manager.process_save)
        self.ui.btn_edit_use_row.clicked.connect(self.load_selected_use_row)
        self.ui.btn_delete_use_row.clicked.connect(self.delete_selected_use_row)
        self.btn_cancel_use_edit.clicked.connect(self.clear_usage_fields)

        self.comboHo.currentTextChanged.connect(self.event_handler.update_floor_corridor_logic)
        self.chkFloorCorridor.stateChanged.connect(self.event_handler.update_floor_corridor_logic)
        
        for i in range(3):
            self.photo_widgets[i]["btn_add"].clicked.connect(lambda checked, idx=i: self.select_photo_file(idx))
            self.photo_widgets[i]["btn_del"].clicked.connect(lambda checked, idx=i: self.remove_photo_selection(idx))

    def update_stock_display(self):
        item_name = self.CB_Item.currentText().strip()
        spec = self.CB_Spec.currentText().strip()
        if item_name and spec:
            try:
                stock = database.get_current_stock(item_name, spec)
                self.LE_CurrentStock.setText(f"{stock:,} 개")
            except:
                self.LE_CurrentStock.setText("조회 오류")
        else:
            self.LE_CurrentStock.clear()

    def select_photo_file(self, idx):
        file_path, _ = QFileDialog.getOpenFileName(self, f"사진 {idx+1} 선택", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.selected_photos[idx] = file_path
            self.photo_widgets[idx]["label"].setText(os.path.basename(file_path))
            self.photo_widgets[idx]["label"].setStyleSheet("color: #2196F3; font-weight: bold;")

    def remove_photo_selection(self, idx):
        self.selected_photos[idx] = None
        self.photo_widgets[idx]["label"].setText(f"사진 {idx+1}: 등록되지 않음")
        self.photo_widgets[idx]["label"].setStyleSheet("color: gray;")

    def show_photo_preview_from_table(self, row, column):
        for i in range(3):
            item = self.tableWidgetUse.item(row, 9 + i)
            file_name = item.text().strip() if item else ""
            if file_name and file_name != "None" and "use_" in file_name:
                full_path = os.path.join(self.image_dir, file_name)
                if os.path.exists(full_path):
                    pixmap = QPixmap(full_path)
                    if not pixmap.isNull():
                        scaled_p = pixmap.scaled(self.lbl_previews[i].width(), self.lbl_previews[i].height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.lbl_previews[i].setPixmap(scaled_p)
                        self.lbl_previews[i].setStyleSheet("border: 1px solid #2196F3; background-color: #FFFFFF;")
                        continue
            self.lbl_previews[i].clear()
            self.lbl_previews[i].setText(f"사진 {i+1} 없음")
            self.lbl_previews[i].setStyleSheet("border: 1px dashed #BDBDBD; background-color: #FAFAFA; color: #9E9E9E; font-size: 11px;")

    def highlight_selected_row(self):
        for r in range(self.tableWidgetUse.rowCount()):
            bg_color = QColor(245, 247, 250) if (r % 4) in [2, 3] else QColor(255, 255, 255)
            for c in range(self.tableWidgetUse.columnCount()):
                item = self.tableWidgetUse.item(r, c)
                if item: item.setBackground(bg_color)
        current_row = self.tableWidgetUse.currentRow()
        if current_row >= 0:
            highlight_color = QColor(255, 224, 178) 
            for c in range(self.tableWidgetUse.columnCount()):
                item = self.tableWidgetUse.item(current_row, c)
                if item: item.setBackground(highlight_color)

    def load_selected_use_row(self):
        current_row = self.tableWidgetUse.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "선택 누락", "수정 편집할 행을 리스트에서 먼저 선택해 주세요.")
            return
        self.data_manager.load_selected_row(current_row)

    def delete_selected_use_row(self):
        current_row = self.tableWidgetUse.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "삭제 오류", "삭제 처리할 행 데이터를 리스트에서 선택해 주세요.")
            return
        if QMessageBox.question(self, '최종 확인', '선택한 사용 내역 기록을 영구 삭제하시겠습니까?', QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.data_manager.delete_row(current_row)

    def clear_usage_fields(self):
        self.is_edit_mode = False
        self.editing_row_id = None
        self.is_loading_row = False
        
        self.chkFloorCorridor.setChecked(False)
        self.dateEditUse.setDate(QDate.currentDate())
        self.comboType.setCurrentIndex(0)
        self.event_handler.handle_type_change("공용")
        
        self.lineEditUseQty.clear()
        self.lineEditUseRemarks.clear()
        self.LE_CurrentStock.clear()  

        self.selected_photos = [None, None, None]
        for i in range(3):
            self.photo_widgets[i]["label"].setText(f"사진 {i+1}: 등록되지 않음")
            self.photo_widgets[i]["label"].setStyleSheet("color: gray;")
            self.lbl_previews[i].clear()
            self.lbl_previews[i].setText(f"사진 {i+1} 없음")
            self.lbl_previews[i].setStyleSheet("border: 1px dashed #BDBDBD; background-color: #FAFAFA; color: #9E9E9E; font-size: 11px;")
        
        self.group_box_use.setTitle("자재 사용(출고) 입력")
        self.btn_save_use.setText("사용 내역 등록")
        self.btn_save_use.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 35px;")
        self.btn_cancel_use_edit.setVisible(False)
        self.tableWidgetUse.clearSelection()

    def table_display_usage(self):
        self.tableWidgetUse.setRowCount(0)
        self.tableWidgetUse.setSortingEnabled(False)
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT use_date, usage_type, dong, ho, discipline, item_name, spec, qty, remarks, photo1, photo2, photo3, worker, id 
            FROM usage_ledger ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        for row_idx, row_data in enumerate(rows):
            self.tableWidgetUse.insertRow(row_idx)
            bg_color = QColor(245, 247, 250) if (row_idx % 4) in [2, 3] else QColor(255, 255, 255)
            
            for col_idx, value in enumerate(row_data):
                if col_idx == 7: 
                    formatted_val = f"{value:,}" if isinstance(value, (int, float)) else str(value)
                    item = QTableWidgetItem(formatted_val)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    
                item.setBackground(bg_color)
                self.tableWidgetUse.setItem(row_idx, col_idx, item)
                
        self.tableWidgetUse.setSortingEnabled(True)
        self.tableWidgetUse.resizeColumnsToContents()
        for col in range(self.tableWidgetUse.columnCount()):
            current_width = self.tableWidgetUse.columnWidth(col)
            self.tableWidgetUse.setColumnWidth(col, current_width + 25)