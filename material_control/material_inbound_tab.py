# material_inbound_tab.py

# material_inbound_tab.py

import sys
import sqlite3
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor, QFont
import database

class InboundTab(QWidget):
    def __init__(self, user_name="미인증"):
        super().__init__()
        self.current_user = user_name
        
        # 수정 모드 및 자동 계산 무한 루프 방지 플래그
        self.is_edit_mode = False
        self.editing_row_id = None  
        self.is_calculating = False  # 양방향 계산 오작동 방지용 플래그

        self.init_ui()
        self.refresh_all_combos() # 콤보박스 전체 초기 로드 (Default 값 자동 세팅 포함)
        self.table_display_in()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # =================================================================
        # 1. 좌측 영역: 입력 폼
        # =================================================================
        left_layout = QVBoxLayout()
        
        self.group_box_in = QGroupBox("자재 입고(등록) 입력")
        grid_in = QGridLayout()
        self.group_box_in.setLayout(grid_in)
        
        # 안내 문구용 공통 폰트 스타일 정의
        notice_font = QFont()
        notice_font.setPointSize(9)
        notice_font.setItalic(True)
        
        # (1) 입고 일자
        grid_in.addWidget(QLabel("입고일자:"), 0, 0)
        self.dateEditIn = QDateEdit()
        self.dateEditIn.setCalendarPopup(True)
        self.dateEditIn.setDate(QDate.currentDate())
        grid_in.addWidget(self.dateEditIn, 0, 1)
        
        # (2) 공종
        grid_in.addWidget(QLabel("공종:"), 1, 0)
        self.comboBoxInDiscipline = QComboBox()  
        self.comboBoxInDiscipline.setEditable(True)
        grid_in.addWidget(self.comboBoxInDiscipline, 1, 1)

        # (3) 품명
        grid_in.addWidget(QLabel("품명:"), 2, 0)
        self.comboBoxInName = QComboBox()        
        self.comboBoxInName.setEditable(True)
        grid_in.addWidget(self.comboBoxInName, 2, 1)
        
        # (4) 규격
        grid_in.addWidget(QLabel("규격:"), 3, 0)
        self.comboBoxInSpec = QComboBox()
        self.comboBoxInSpec.setEditable(True)
        grid_in.addWidget(self.comboBoxInSpec, 3, 1)
        
        # [추가] 콤보박스 하단 신규 품목 직접 입력 안내 문구 (4행 전체 병합)
        self.lbl_combo_notice = QLabel("※ 리스트에 없는 신규 품종(품명, 규격, 공종)은\n    콤보박스에 직접 타이핑하여 입력하시면 됩니다.")
        self.lbl_combo_notice.setFont(notice_font)
        self.lbl_combo_notice.setStyleSheet("color: #1976D2; margin-top: 2px; margin-bottom: 8px; line-height: 140%;")
        grid_in.addWidget(self.lbl_combo_notice, 4, 0, 1, 2)
        
        # (5) 입고 수량
        grid_in.addWidget(QLabel("입고수량:"), 5, 0)
        self.lineEditInQty = QLineEdit()
        grid_in.addWidget(self.lineEditInQty, 5, 1)
        
        # (6) 단가
        grid_in.addWidget(QLabel("단가:"), 6, 0)
        self.lineEditInPrice = QLineEdit()
        grid_in.addWidget(self.lineEditInPrice, 6, 1)
        
        # [추가] 단가와 총금액 사이 양방향 계산 기능 안내 문구 (7행 전체 병합)
        self.lbl_price_notice = QLabel("💡 단가 또는 총금액 중 '하나만 입력'하셔도\n    수량에 맞춰 나머지 금액이 자동 역산됩니다.")
        self.lbl_price_notice.setFont(notice_font)
        self.lbl_price_notice.setStyleSheet("color: #2E7D32; margin-top: 4px; margin-bottom: 4px; line-height: 140%;")
        grid_in.addWidget(self.lbl_price_notice, 7, 0, 1, 2)
        
        # (7) 총금액
        grid_in.addWidget(QLabel("총금액:"), 8, 0)
        self.lineEditInTotalPrice = QLineEdit()
        grid_in.addWidget(self.lineEditInTotalPrice, 8, 1)

        # (8) 공급처
        grid_in.addWidget(QLabel("공급처:"), 9, 0)
        self.lineEditInSupplier = QLineEdit()
        grid_in.addWidget(self.lineEditInSupplier, 9, 1)
        
        # (9) 비고
        grid_in.addWidget(QLabel("비고:"), 10, 0)
        self.lineEditInRemarks = QLineEdit()
        grid_in.addWidget(self.lineEditInRemarks, 10, 1)
        
        # (10) 버튼 영역
        button_layout = QHBoxLayout()
        self.btn_save_in = QPushButton("입고 내역 등록")
        self.btn_save_in.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 35px;")
        self.btn_save_in.clicked.connect(self.process_inbound_save)
        button_layout.addWidget(self.btn_save_in)
        
        self.btn_cancel_edit = QPushButton("수정 취소")
        self.btn_cancel_edit.setStyleSheet("background-color: #757575; color: white; font-weight: bold; height: 35px;")
        self.btn_cancel_edit.setVisible(False)
        self.btn_cancel_edit.clicked.connect(self.clear_input_fields)
        button_layout.addWidget(self.btn_cancel_edit)
        
        grid_in.addLayout(button_layout, 11, 0, 1, 2)
        
        left_layout.addWidget(self.group_box_in)
        left_layout.addStretch()
        
        # =================================================================
        # 2. 우측 영역: 테이블 및 관리 버튼
        # =================================================================
        right_layout = QVBoxLayout()
        
        top_bar = QHBoxLayout()
        self.btn_edit_row = QPushButton("선택 내역 수정")
        self.btn_edit_row.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 6px 12px;")
        self.btn_edit_row.clicked.connect(self.load_selected_row_to_form)
        top_bar.addWidget(self.btn_edit_row)
        
        self.btn_delete_in = QPushButton("선택 내역 삭제")
        self.btn_delete_in.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px 12px;")
        self.btn_delete_in.clicked.connect(self.delete_selected_row)
        top_bar.addWidget(self.btn_delete_in)
        
        top_bar.addStretch()
        right_layout.addLayout(top_bar)
        
        self.tableWidgetInIn = QTableWidget()
        self.tableWidgetInIn.setColumnCount(10)
        self.tableWidgetInIn.setHorizontalHeaderLabels([
            "입고일자", "공종", "품명", "규격", "수량", "단가", "총금액", "공급처", "비고", "입력자"
        ])
        self.tableWidgetInIn.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidgetInIn.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.tableWidgetInIn)
        
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)

        # 시그널 연결 (품명 변경 동기화 및 실시간 금액 양방향 계산)
        self.comboBoxInName.currentTextChanged.connect(self.sync_spec_combo)
        self.lineEditInQty.textChanged.connect(self.calculate_from_price)
        self.lineEditInPrice.textChanged.connect(self.calculate_from_price)
        self.lineEditInTotalPrice.textChanged.connect(self.calculate_from_total_price)

    # =================================================================
    # 금액/단가 실시간 양방향 자동 계산 로직
    # =================================================================
    def calculate_from_price(self):
        if self.is_calculating:
            return
        if not (self.lineEditInQty.hasFocus() or self.lineEditInPrice.hasFocus()):
            return

        qty_str = self.lineEditInQty.text().strip()
        price_str = self.lineEditInPrice.text().strip()

        if qty_str.isdigit() and price_str.isdigit():
            qty = int(qty_str)
            price = int(price_str)
            self.is_calculating = True
            self.lineEditInTotalPrice.setText(str(qty * price))
            self.is_calculating = False
        elif not qty_str or not price_str:
            self.is_calculating = True
            self.lineEditInTotalPrice.clear()
            self.is_calculating = False

    def calculate_from_total_price(self):
        if self.is_calculating:
            return
        if not self.lineEditInTotalPrice.hasFocus():
            return

        qty_str = self.lineEditInQty.text().strip()
        total_price_str = self.lineEditInTotalPrice.text().strip()

        if qty_str.isdigit() and total_price_str.isdigit():
            qty = int(qty_str)
            total_price = int(total_price_str)
            if qty > 0:
                unit_price = total_price // qty
                self.is_calculating = True
                self.lineEditInPrice.setText(str(unit_price))
                self.is_calculating = False
            else:
                self.is_calculating = True
                self.lineEditInPrice.clear()
                self.is_calculating = False
        elif not total_price_str:
            self.is_calculating = True
            self.lineEditInPrice.clear()
            self.is_calculating = False

    # =================================================================
    # 데이터 흐름 제어 및 저장 로직
    # =================================================================
    def process_inbound_save(self):
        discipline = self.comboBoxInDiscipline.currentText().strip()
        item_name = self.comboBoxInName.currentText().strip()
        spec = self.comboBoxInSpec.currentText().strip()
        qty_str = self.lineEditInQty.text().strip()
        price_str = self.lineEditInPrice.text().strip()
        total_price_str = self.lineEditInTotalPrice.text().strip()
        
        if not item_name:
            QMessageBox.warning(self, "입력 오류", "품명을 선택하거나 입력해 주세요.")
            return
        if not qty_str or not qty_str.isdigit():
            QMessageBox.warning(self, "입력 오류", "정확한 입고 수량을 숫자로 입력해 주세요.")
            return

        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM material_items WHERE item_name = %s", (item_name,))
        item_exists = cursor.fetchone()[0] > 0
        
        if not item_exists:
            if not spec:
                QMessageBox.information(
                    self, 
                    "신규 품명 안내", 
                    f"[{item_name}]은(는) 처음 등록되는 신규 품명입니다.\n새로운 규격을 하단에 입력해 주세요."
                )
                self.comboBoxInSpec.clearEditText()
                self.comboBoxInSpec.setFocus()
                conn.close()
                return

        cursor.execute("SELECT COUNT(*) FROM material_items WHERE item_name = %s AND spec = %s", (item_name, spec))
        pair_exists = cursor.fetchone()[0] > 0
        
        if not pair_exists:
            reply = QMessageBox.question(
                self,
                "신규 자재 등록 확인",
                f"시스템 마스터에 없는 새로운 자재 정보입니다.\n\n"
                f"▶ 품명: {item_name}\n"
                f"▶ 규격: {spec}\n\n"
                f"위 정보가 정확합니까%s 확인 후 등록됩니다.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                conn.close()
                return
            
            try:
                cursor.execute("INSERT INTO material_items (item_name, spec) VALUES (%s, %s)", (item_name, spec))
                conn.commit()
            except sqlite3.IntegrityError:
                pass

        conn.close()

        qty = int(qty_str)
        total_price = int(total_price_str) if total_price_str.isdigit() else 0
        unit_price = int(price_str) if price_str.isdigit() else 0
        
        supplier = self.lineEditInSupplier.text().strip()
        remarks = self.lineEditInRemarks.text().strip()
        in_date = self.dateEditIn.date().toString("yyyy-MM-dd")
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        if self.is_edit_mode:
            cursor.execute("""
                UPDATE inbound_ledger
                SET in_date=%s, discipline=%s, item_name=%s, spec=%s, qty=%s, unit_price=%s, total_price=%s, supplier=%s, remarks=%s, worker=%s
                WHERE id = %s
            """, (in_date, discipline, item_name, spec, qty, unit_price, total_price, supplier, remarks, self.current_user, self.editing_row_id))
            conn.commit()
            QMessageBox.information(self, "수정 완료", "자재 입고 내역이 정상적으로 수정되었습니다.")
        else:
            cursor.execute("""
                INSERT INTO inbound_ledger (in_date, discipline, item_name, spec, qty, unit_price, total_price, supplier, remarks, worker)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (in_date, discipline, item_name, spec, qty, unit_price, total_price, supplier, remarks, self.current_user))
            conn.commit()
            QMessageBox.information(self, "등록 완료", "입고 내역이 등록되었습니다.")
            
        conn.close()
        
        self.clear_input_fields()
        self.refresh_all_combos() 
        self.table_display_in()

    def load_selected_row_to_form(self):
        current_row = self.tableWidgetInIn.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "선택 오류", "수정할 입고 내역 행을 테이블에서 선택해 주세요.")
            return
            
        in_date_str = self.tableWidgetInIn.item(current_row, 0).text()
        discipline = self.tableWidgetInIn.item(current_row, 1).text()
        item_name = self.tableWidgetInIn.item(current_row, 2).text()
        spec = self.tableWidgetInIn.item(current_row, 3).text()
        qty = self.tableWidgetInIn.item(current_row, 4).text().replace(",", "")
        unit_price = self.tableWidgetInIn.item(current_row, 5).text().replace(",", "")
        total_price = self.tableWidgetInIn.item(current_row, 6).text().replace(",", "")
        supplier = self.tableWidgetInIn.item(current_row, 7).text()
        remarks = self.tableWidgetInIn.item(current_row, 8).text()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM inbound_ledger 
            WHERE in_date=%s AND item_name=%s AND spec=%s AND qty=%s AND supplier=%s
            ORDER BY id DESC LIMIT 1
        """, (in_date_str, item_name, spec, int(qty), supplier))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            self.is_edit_mode = True
            self.editing_row_id = result[0]
            
            self.dateEditIn.setDate(QDate.fromString(in_date_str, "yyyy-MM-dd"))
            self.comboBoxInDiscipline.setEditText(discipline)
            self.comboBoxInName.setEditText(item_name)
            self.comboBoxInSpec.setEditText(spec)
            
            self.is_calculating = True
            self.lineEditInQty.setText(qty)
            self.lineEditInPrice.setText(unit_price)
            self.lineEditInTotalPrice.setText(total_price)
            self.is_calculating = False
            
            self.lineEditInSupplier.setText(supplier)
            self.lineEditInRemarks.setText(remarks)
            
            self.group_box_in.setTitle("⚠️ 자재 입고 내역 수정 중")
            self.btn_save_in.setText("수정 완료 저장")
            self.btn_save_in.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; height: 35px;")
            self.btn_cancel_edit.setVisible(True)

    def clear_input_fields(self):
        self.is_edit_mode = False
        self.editing_row_id = None
        
        self.dateEditIn.setDate(QDate.currentDate())
        self.comboBoxInDiscipline.clearEditText()
        self.comboBoxInName.clearEditText()
        self.comboBoxInSpec.clearEditText()
        
        self.is_calculating = True
        self.lineEditInQty.clear()
        self.lineEditInPrice.clear()
        self.lineEditInTotalPrice.clear()
        self.is_calculating = False
        
        self.lineEditInSupplier.clear()
        self.lineEditInRemarks.clear()
        
        self.group_box_in.setTitle("자재 입고(등록) 입력")
        self.btn_save_in.setText("입고 내역 등록")
        self.btn_save_in.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 35px;")
        self.btn_cancel_edit.setVisible(False)

    def refresh_all_combos(self):
        self.comboBoxInName.blockSignals(True)
        self.comboBoxInName.clear()
        self.comboBoxInDiscipline.blockSignals(True)
        self.comboBoxInDiscipline.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT item_name FROM material_items ORDER BY item_name ASC")
        items = cursor.fetchall()
        for i in items:
            self.comboBoxInName.addItem(str(i[0]))
            
        cursor.execute("SELECT DISTINCT discipline FROM inbound_ledger WHERE discipline IS NOT NULL AND discipline != '' ORDER BY discipline ASC")
        disciplines = cursor.fetchall()
        for d in disciplines:
            self.comboBoxInDiscipline.addItem(str(d[0]))
            
        cursor.execute("""
            SELECT discipline, item_name, spec 
            FROM inbound_ledger 
            ORDER BY id DESC LIMIT 1
        """)
        last_entry = cursor.fetchone()
        conn.close()
        
        self.comboBoxInName.blockSignals(False)
        self.comboBoxInDiscipline.blockSignals(False)
        
        if last_entry and not self.is_edit_mode:
            default_discipline = str(last_entry[0]) if last_entry[0] else ""
            default_item_name = str(last_entry[1]) if last_entry[1] else ""
            default_spec = str(last_entry[2]) if last_entry[2] else ""
            
            self.comboBoxInDiscipline.setEditText(default_discipline)
            self.comboBoxInName.setEditText(default_item_name)
            self.sync_spec_combo(default_item_name)
            self.comboBoxInSpec.setEditText(default_spec)
        else:
            if not self.is_edit_mode:
                self.comboBoxInName.clearEditText()
                self.comboBoxInDiscipline.clearEditText()
                self.comboBoxInSpec.clear()

    def sync_spec_combo(self, item_name):
        if not item_name:
            return
        self.comboBoxInSpec.blockSignals(True)
        self.comboBoxInSpec.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT spec FROM material_items WHERE item_name = %s ORDER BY spec ASC", (item_name,))
        specs = cursor.fetchall()
        conn.close()
        
        for s in specs:
            self.comboBoxInSpec.addItem(str(s[0]))
            
        self.comboBoxInSpec.blockSignals(False)
        if not self.is_edit_mode:
            self.comboBoxInSpec.clearEditText()

    def table_display_in(self):
        self.tableWidgetInIn.setRowCount(0)
        self.tableWidgetInIn.setSortingEnabled(False)
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT in_date, discipline, item_name, spec, qty, unit_price, total_price, supplier, remarks, worker 
            FROM inbound_ledger 
            ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        for row_idx, row_data in enumerate(rows):
            self.tableWidgetInIn.insertRow(row_idx)
            bg_color = QColor(245, 247, 250) if (row_idx % 4) in [2, 3] else QColor(255, 255, 255)
            
            for col_idx, value in enumerate(row_data):
                if col_idx in [4, 5, 6]: 
                    formatted_val = f"{value:,}" if isinstance(value, (int, float)) else str(value)
                    item = QTableWidgetItem(formatted_val)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setTextAlignment(Qt.AlignCenter)
                
                item.setBackground(bg_color)
                self.tableWidgetInIn.setItem(row_idx, col_idx, item)
                
        self.tableWidgetInIn.setSortingEnabled(True)
        self.tableWidgetInIn.resizeColumnsToContents()
        for col in range(self.tableWidgetInIn.columnCount()):
            current_width = self.tableWidgetInIn.columnWidth(col)
            self.tableWidgetInIn.setColumnWidth(col, current_width + 25)

    def delete_selected_row(self):
        current_row = self.tableWidgetInIn.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "삭제 오류", "삭제할 항목을 선택해 주세요.")
            return
        if QMessageBox.question(self, '확인', '선택한 내역을 삭제하시겠습니까%s', QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            in_date = self.tableWidgetInIn.item(current_row, 0).text()
            item_name = self.tableWidgetInIn.item(current_row, 2).text() 
            spec = self.tableWidgetInIn.item(current_row, 3).text()      
            qty = int(self.tableWidgetInIn.item(current_row, 4).text().replace(",", "")) 
            
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM inbound_ledger 
                WHERE in_date=%s AND item_name=%s AND spec=%s AND qty=%s
            """, (in_date, item_name, spec, qty))
            conn.commit()
            conn.close()
            
            if self.is_edit_mode:
                self.clear_input_fields()
                
            self.table_display_in()
            self.refresh_all_combos() 
            QMessageBox.information(self, "성공", "선택한 내역이 삭제되었습니다.")