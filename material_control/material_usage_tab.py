# material_usage_tab.py
import sys
import sqlite3
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor
import database
from material_usage_ui import UsageTabUI  # UI 템플릿 임포트

class UsageTab(QWidget):
    def __init__(self, user_name="미인증"):
        super().__init__()
        self.current_user = user_name
        
        self.is_edit_mode = False
        self.editing_row_id = None
        self.is_loading_row = False 
        self.is_syncing_ho_disp = False # [추가] 공용 상태 양방향 연동 무한루프 방지 플래그

        # 1. UI 스킨 결합 및 변수 참조 연결
        self.ui = UsageTabUI()
        self.ui.setup_ui(self)
        self.bind_ui_variables()

        # 2. 시그널 바인딩 및 데이터 로드
        self.connect_signals()
        self.init_combobox_data()
        self.table_display_usage()

    def bind_ui_variables(self):
        """UI 파일의 컴포넌트들을 기존 로직 변수명과 일치시켜 소스 수정 최소화"""
        self.comboType = self.ui.comboType
        self.comboDong = self.ui.comboDong
        self.comboHo = self.ui.comboHo
        self.comboDiscipline = self.ui.comboDiscipline
        self.CB_Item = self.ui.CB_Item
        self.CB_Spec = self.ui.CB_Spec
        self.LE_CurrentStock = self.ui.LE_CurrentStock
        self.lineEditUseQty = self.ui.lineEditUseQty
        self.lineEditUseRemarks = self.ui.lineEditUseRemarks
        self.tableWidgetUse = self.ui.tableWidgetUse
        self.group_box_use = self.ui.group_box_use
        self.btn_save_use = self.ui.btn_save_use
        self.btn_cancel_use_edit = self.ui.btn_cancel_use_edit
        self.dateEditUse = self.ui.dateEditUse

    def connect_signals(self):
        """UI 컴포넌트 기능과 파이썬 메서드 연결"""
        self.comboType.currentTextChanged.connect(self.handle_type_change)
        self.comboDong.currentTextChanged.connect(self.handle_dong_change)
        
        # [수정] 호수와 공종의 변경 감지 시그널을 상호 연동 핸들러 함수로 연결
        self.comboHo.currentTextChanged.connect(self.handle_ho_change)
        self.comboDiscipline.currentTextChanged.connect(self.handle_discipline_change)
        
        self.CB_Item.currentTextChanged.connect(self.handle_item_change)
        self.CB_Spec.currentTextChanged.connect(self.update_stock_display)
        self.tableWidgetUse.itemSelectionChanged.connect(self.highlight_selected_row)
        
        # 버튼 처리 시그널 연결
        self.btn_save_use.clicked.connect(self.process_usage_save)
        self.ui.btn_edit_use_row.clicked.connect(self.load_selected_use_row)
        self.ui.btn_delete_use_row.clicked.connect(self.delete_selected_use_row)
        self.btn_cancel_use_edit.clicked.connect(self.clear_usage_fields)

    # =================================================================
    # 비즈니스 데이터 처리 및 연동 로직 코드
    # =================================================================
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

    def init_combobox_data(self):
        self.handle_type_change(self.comboType.currentText())

    def handle_type_change(self, current_type):
        if self.is_loading_row:
            return
        self.comboDong.blockSignals(True)
        self.comboDong.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT dong FROM dongho_master ORDER BY CAST(dong AS INTEGER) ASC, dong ASC")
        dongs = [str(d[0]) for d in cursor.fetchall()]
        conn.close()
        
        for d in dongs:
            self.comboDong.addItem(d)
            
        if current_type == "공용":
            if "999" not in dongs:
                self.comboDong.addItem("999")
            self.comboDong.blockSignals(False)
            self.comboDong.setCurrentText("999") 
            self.handle_dong_change("999")
        else:
            index = self.comboDong.findText("101")
            self.comboDong.blockSignals(False)
            if index >= 0:
                self.comboDong.setCurrentIndex(index) 
            else:
                self.comboDong.setCurrentIndex(0)
            self.handle_dong_change(self.comboDong.currentText())

    def handle_dong_change(self, selected_dong):
        if not selected_dong or self.is_loading_row:
            return
        self.sync_ho_combo(selected_dong)
        
        if selected_dong == "999":
            self.comboDiscipline.blockSignals(True)
            self.comboDiscipline.clear()
            for i in range(self.comboHo.count()):
                self.comboDiscipline.addItem(self.comboHo.itemText(i))
            self.comboDiscipline.blockSignals(False)
            
            if self.comboHo.count() > 0:
                first_ho_text = self.comboHo.itemText(0)
                self.comboDiscipline.setCurrentText(first_ho_text)
                self.sync_items_by_discipline(first_ho_text)
        else:
            self.comboDiscipline.blockSignals(True)
            self.comboDiscipline.clear()
            
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT discipline FROM inbound_ledger WHERE discipline IS NOT NULL AND discipline != '' ORDER BY discipline ASC")
            disciplines = cursor.fetchall()
            conn.close()
            
            for disp in disciplines:
                self.comboDiscipline.addItem(str(disp[0]))
                
            self.comboDiscipline.blockSignals(False)
            if self.comboDiscipline.count() > 0:
                self.comboDiscipline.setCurrentIndex(0)
                self.sync_items_by_discipline(self.comboDiscipline.currentText())

    # [핵심 기능 수정] 호수 변경 시 공종 양방향 동기화
    def handle_ho_change(self, selected_ho):
        if not selected_ho or self.is_loading_row or self.is_syncing_ho_disp:
            return
            
        if self.comboType.currentText() == "공용" and self.comboDong.currentText() == "999":
            self.is_syncing_ho_disp = True
            self.comboDiscipline.setCurrentText(selected_ho)
            self.is_syncing_ho_disp = False
            self.sync_items_by_discipline(selected_ho)

    # [핵심 기능 수정] 공종 변경 시 호수 양방향 동기화
    def handle_discipline_change(self, selected_disp):
        if not selected_disp or self.is_loading_row or self.is_syncing_ho_disp:
            return
            
        if self.comboType.currentText() == "공용" and self.comboDong.currentText() == "999":
            self.is_syncing_ho_disp = True
            self.comboHo.setCurrentText(selected_disp)
            self.is_syncing_ho_disp = False
            
        self.sync_items_by_discipline(selected_disp)

    def sync_ho_combo(self, selected_dong):
        if not selected_dong or self.is_loading_row:
            return
        self.comboHo.blockSignals(True)
        self.comboHo.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ho FROM dongho_master WHERE dong = ? ORDER BY CAST(ho AS INTEGER) ASC, ho ASC", (selected_dong,))
        hos = cursor.fetchall()
        conn.close()
        
        for h in hos:
            self.comboHo.addItem(str(h[0]))
            
        if self.comboHo.count() > 0:
            self.comboHo.setCurrentIndex(0) 
        self.comboHo.blockSignals(False)

    def sync_items_by_discipline(self, discipline):
        if self.is_loading_row or not discipline:
            return
        self.CB_Item.blockSignals(True)
        self.CB_Item.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT item_name FROM inbound_ledger WHERE discipline = ? ORDER BY item_name ASC", (discipline,))
        items = cursor.fetchall()
        conn.close()
        
        for i in items:
            self.CB_Item.addItem(str(i[0]))
            
        self.CB_Item.blockSignals(False)
        self.handle_item_change(self.CB_Item.currentText())

    def handle_item_change(self, item_name):
        if self.is_loading_row or not item_name:
            self.LE_CurrentStock.clear()
            return
        self.sync_specs_by_item(item_name)
        self.update_stock_display()

    def sync_specs_by_item(self, item_name):
        if not item_name or self.is_loading_row:
            return
        self.CB_Spec.blockSignals(True)
        self.CB_Spec.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT spec FROM inbound_ledger 
            WHERE discipline = ? AND item_name = ? ORDER BY spec ASC
        """, (self.comboDiscipline.currentText(), item_name))
        specs = cursor.fetchall()
        conn.close()
        
        for s in specs:
            self.CB_Spec.addItem(str(s[0]))
        self.CB_Spec.blockSignals(False)

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

    def process_usage_save(self):
        use_date = self.dateEditUse.date().toString("yyyy-MM-dd")
        usage_type = self.comboType.currentText()
        dong = self.comboDong.currentText().strip()
        ho = self.comboHo.currentText().strip()
        discipline = self.comboDiscipline.currentText().strip()
        item_name = self.CB_Item.currentText().strip()
        spec = self.CB_Spec.currentText().strip()
        qty_str = self.lineEditUseQty.text().strip()
        remarks = self.lineEditUseRemarks.text().strip()
        
        if not item_name:
            QMessageBox.warning(self, "입력 오류", "사용할 자재 품명을 선택해 주세요.")
            return
        if not qty_str or not qty_str.isdigit() or int(qty_str) <= 0:
            QMessageBox.warning(self, "입력 오류", "사용 수량은 1개 이상의 숫자로 입력해야 합니다.")
            return
            
        qty = int(qty_str)
        
        try:
            current_stock = database.get_current_stock(item_name, spec)
            if self.is_edit_mode:
                conn = database.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT qty FROM usage_ledger WHERE id = ?", (self.editing_row_id,))
                old_qty_res = cursor.fetchone()
                conn.close()
                if old_qty_res: current_stock += old_qty_res[0]

            if qty > current_stock:
                QMessageBox.warning(self, "재고 부족", f"현재 남은 재고({current_stock}개)보다 출고 수량({qty}개)이 더 많습니다.")
                return
        except:
            pass
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        if self.is_edit_mode:
            cursor.execute("""
                UPDATE usage_ledger
                SET use_date=?, usage_type=?, dong=?, ho=?, discipline=?, item_name=?, spec=?, qty=?, remarks=?, worker=?
                WHERE id = ?
            """, (use_date, usage_type, dong, ho, discipline, item_name, spec, qty, remarks, self.current_user, self.editing_row_id))
            conn.commit()
            QMessageBox.information(self, "수정 성공", "자재 출고/사용 내역 수정이 완료되었습니다.")
        else:
            cursor.execute("""
                INSERT INTO usage_ledger (use_date, usage_type, dong, ho, discipline, item_name, spec, qty, remarks, worker)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (use_date, usage_type, dong, ho, discipline, item_name, spec, qty, remarks, self.current_user))
            conn.commit()
            QMessageBox.information(self, "등록 성공", "자재 사용 내역이 대장에 기록되었습니다.")
        conn.close()
        
        self.clear_usage_fields()
        self.table_display_usage()

    def load_selected_use_row(self):
        current_row = self.tableWidgetUse.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "선택 누락", "수정 편집할 행을 리스트에서 먼저 선택해 주세요.")
            return
            
        use_date_str = self.tableWidgetUse.item(current_row, 0).text()
        usage_type = self.tableWidgetUse.item(current_row, 1).text()
        dong = self.tableWidgetUse.item(current_row, 2).text()
        ho = self.tableWidgetUse.item(current_row, 3).text()
        discipline = self.tableWidgetUse.item(current_row, 4).text()
        item_name = self.tableWidgetUse.item(current_row, 5).text()
        spec = self.tableWidgetUse.item(current_row, 6).text()
        qty = self.tableWidgetUse.item(current_row, 7).text().replace(",", "")
        remarks = self.tableWidgetUse.item(current_row, 8).text()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM usage_ledger 
            WHERE use_date=? AND usage_type=? AND dong=? AND ho=? AND item_name=? AND qty=?
            ORDER BY id DESC LIMIT 1
        """, (use_date_str, usage_type, dong, ho, item_name, int(qty)))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            self.is_edit_mode = True
            self.editing_row_id = result[0]
            self.is_loading_row = True 
            
            self.dateEditUse.setDate(QDate.fromString(use_date_str, "yyyy-MM-dd"))
            self.comboType.setCurrentText(usage_type)
            self.comboDong.setCurrentText(dong)
            if usage_type == "공용":
                self.comboHo.clear()
                conn = database.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT ho FROM dongho_master WHERE dong = '999'")
                for h in cursor.fetchall(): self.comboHo.addItem(str(h[0]))
                conn.close()
            else:
                self.sync_ho_combo(dong)
            self.comboHo.setCurrentText(ho)
            
            self.comboDiscipline.setCurrentText(discipline)
            self.sync_items_by_discipline(discipline)
            self.CB_Item.setCurrentText(item_name)
            self.sync_specs_by_item(item_name)
            self.CB_Spec.setCurrentText(spec)
            
            self.lineEditUseQty.setText(qty)
            self.lineEditUseRemarks.setText(remarks)
            
            self.is_loading_row = False 
            self.update_stock_display()
            
            self.group_box_use.setTitle("⚠️ 자재 사용 내역 수정 모드")
            self.btn_save_use.setText("수정 완료 저장")
            self.btn_save_use.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; height: 35px;")
            self.btn_cancel_use_edit.setVisible(True)

    def clear_usage_fields(self):
        self.is_edit_mode = False
        self.editing_row_id = None
        self.is_loading_row = False
        
        self.dateEditUse.setDate(QDate.currentDate())
        self.comboType.setCurrentIndex(0)
        self.handle_type_change("공용")
        
        self.lineEditUseQty.clear()
        self.lineEditUseRemarks.clear()
        self.LE_CurrentStock.clear()  
        
        self.group_box_use.setTitle("자재 사용(출고) 입력")
        self.btn_save_use.setText("사용 내역 등록")
        self.btn_save_use.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 35px;")
        self.btn_cancel_use_edit.setVisible(False)
        self.tableWidgetUse.clearSelection()

    def delete_selected_use_row(self):
        current_row = self.tableWidgetUse.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "삭제 오류", "삭제 처리할 행 데이터를 리스트에서 선택해 주세요.")
            return
            
        if QMessageBox.question(self, '최종 확인', '선택한 사용 내역 기록을 영구 삭제하시겠습니까?', QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            use_date = self.tableWidgetUse.item(current_row, 0).text()
            dong = self.tableWidgetUse.item(current_row, 2).text()
            ho = self.tableWidgetUse.item(current_row, 3).text()
            item_name = self.tableWidgetUse.item(current_row, 5).text()
            qty = int(self.tableWidgetUse.item(current_row, 7).text().replace(",", ""))
            
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM usage_ledger 
                WHERE use_date=? AND dong=? AND ho=? AND item_name=? AND qty=?
            """, (use_date, dong, ho, item_name, qty))
            conn.commit()
            conn.close()
            
            if self.is_edit_mode: self.clear_usage_fields()
            self.table_display_usage()
            QMessageBox.information(self, "삭제 성공", "선택 정보가 사용 대장에서 정상 제외되었습니다.")

    def table_display_usage(self):
        self.tableWidgetUse.setRowCount(0)
        self.tableWidgetUse.setSortingEnabled(False)
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT use_date, usage_type, dong, ho, discipline, item_name, spec, qty, remarks, worker 
            FROM usage_ledger 
            ORDER BY id DESC
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