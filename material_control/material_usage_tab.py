# material_usage_tab.py

import sys
import sqlite3
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor, QFont
import database

class UsageTab(QWidget):
    def __init__(self, user_name="미인증"):
        super().__init__()
        self.current_user = user_name
        
        # 수정 모드 및 무한 시그널 루프 방지 플래그
        self.is_edit_mode = False
        self.editing_row_id = None
        self.is_loading_row = False 

        self.init_ui()
        self.init_combobox_data()
        self.table_display_usage()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
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
        
        # 콤보박스 연동 안내 노티스
        self.lbl_usage_notice = QLabel("💡 공종을 선택하면 해당 공종의 품명만 필터링되며,\n    품명을 선택하면 사용 가능한 규격이 나타납니다.")
        self.lbl_usage_notice.setFont(notice_font)
        self.lbl_usage_notice.setStyleSheet("color: #1976D2; margin-top: 2px; margin-bottom: 5px;")
        grid_use.addWidget(self.lbl_usage_notice, 7, 0, 1, 2)
        
        # (7) 현재 재고 현황 표시창 (사용수량 바로 위에 배치)
        grid_use.addWidget(QLabel("현재 재고:"), 8, 0)
        self.LE_CurrentStock = QLineEdit()
        self.LE_CurrentStock.setReadOnly(True)  # 읽기 전용 설정
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
        self.btn_save_use.clicked.connect(self.process_usage_save)
        button_layout.addWidget(self.btn_save_use)
        
        self.btn_cancel_use_edit = QPushButton("수정 취소")
        self.btn_cancel_use_edit.setStyleSheet("background-color: #757575; color: white; font-weight: bold; height: 35px;")
        self.btn_cancel_use_edit.setVisible(False)
        self.btn_cancel_use_edit.clicked.connect(self.clear_usage_fields)
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
        self.btn_edit_use_row.clicked.connect(self.load_selected_use_row)
        top_bar.addWidget(self.btn_edit_use_row)
        
        self.btn_delete_use_row = QPushButton("선택 내역 삭제")
        self.btn_delete_use_row.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px 12px;")
        self.btn_delete_use_row.clicked.connect(self.delete_selected_use_row)
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

        # --------------------------------------------------
        # 시그널 연동 정의 (정밀 조정)
        # --------------------------------------------------
        self.comboType.currentTextChanged.connect(self.handle_type_change)
        self.comboDong.currentTextChanged.connect(self.sync_ho_combo)
        
        # 대분류 공종이 바뀌면 품명을 바인딩
        self.comboDiscipline.currentTextChanged.connect(self.sync_items_by_discipline)
        
        # 품명(CB_Item)이나 규격(CB_Spec)이 바뀔 때 실시간 재고 연쇄 동기화
        self.CB_Item.currentTextChanged.connect(self.handle_item_change)
        self.CB_Spec.currentTextChanged.connect(self.update_stock_display)
        
        # 테이블 선택 변경 시 실시간 라인 하이라이트 효과 적용
        self.tableWidgetUse.itemSelectionChanged.connect(self.highlight_selected_row)

    # =================================================================
    # 실시간 재고 현황 조회 및 표시 함수
    # =================================================================
    def update_stock_display(self):
        """현재 선택된 품명과 규격을 바탕으로 재고를 조회하여 표시"""
        item_name = self.CB_Item.currentText().strip()
        spec = self.CB_Spec.currentText().strip()
        
        if item_name and spec:
            try:
                stock = database.get_current_stock(item_name, spec)
                self.LE_CurrentStock.setText(f"{stock:,} 개")
            except Exception as e:
                self.LE_CurrentStock.setText("조회 오류")
        else:
            self.LE_CurrentStock.clear()

    # =================================================================
    # 데이터 연동 및 동적 필터링 로직
    # =================================================================
    def init_combobox_data(self):
        """초기 기동 시 마스터 DB에서 데이터를 읽어와 대분류(구분, 동, 공종)를 세팅합니다."""
        self.comboDong.blockSignals(True)
        self.comboDiscipline.blockSignals(True)
        self.comboDong.clear()
        self.comboDiscipline.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT dong FROM dongho_master ORDER BY CAST(dong AS INTEGER) ASC, dong ASC")
        dongs = cursor.fetchall()
        for d in dongs:
            self.comboDong.addItem(str(d[0]))
            
        cursor.execute("SELECT DISTINCT discipline FROM inbound_ledger WHERE discipline IS NOT NULL AND discipline != '' ORDER BY discipline ASC")
        disciplines = cursor.fetchall()
        conn.close()
        
        for disp in disciplines:
            self.comboDiscipline.addItem(str(disp[0]))
            
        self.comboDong.blockSignals(False)
        self.comboDiscipline.blockSignals(False)
        
        # 기본값 로드 연쇄 가동
        self.handle_type_change(self.comboType.currentText())
        self.sync_items_by_discipline(self.comboDiscipline.currentText())

    def handle_type_change(self, current_type):
        """구분이 변경되면 요구사항에 따라 동/호를 자동으로 초기화하지만, 목록은 유지합니다."""
        if self.is_loading_row:
            return
            
        self.comboDong.blockSignals(True)
        self.comboHo.blockSignals(True)
        
        # 1. DB 전체 동 리스트를 깨끗하게 다시 채웁니다.
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
            self.comboDong.setCurrentText("999")
            
            # [수정] 호수 목록을 강제로 999 하나로 잠그지 않고, 위의 sync_ho_combo를 호출하여 999동의 전체 목록을 로드합니다.
            self.comboDong.blockSignals(False)
            self.sync_ho_combo("999")
        else:
            index = self.comboDong.findText("101")
            if index >= 0:
                self.comboDong.setCurrentIndex(index)
            else:
                self.comboDong.setCurrentIndex(0)
                
            self.comboDong.blockSignals(False)
            self.sync_ho_combo(self.comboDong.currentText())
            
        self.comboDong.blockSignals(False)
        self.comboHo.blockSignals(False)
    def sync_ho_combo(self, selected_dong):
        """선택된 동에 거주하는 호 리스트(999동의 경우 공종 명칭들)를 동적으로 바인딩합니다."""
        if not selected_dong or self.is_loading_row:
            return
            
        self.comboHo.blockSignals(True)
        self.comboHo.clear()
        
        # 999동이든 일반 동이든 관계없이 DB(dongho_master)에서 실제 호수 데이터만 조회합니다.
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ho FROM dongho_master 
            WHERE dong = ? 
            ORDER BY CAST(ho AS INTEGER) ASC, ho ASC
        """, (selected_dong,))
        hos = cursor.fetchall()
        conn.close()
        
        # DB에서 가져온 호수(전기, 기계, 커뮤니티, 또는 일반 호수)를 콤보박스에 추가
        for h in hos:
            self.comboHo.addItem(str(h[0]))
            
        # [삭제 완료] 호수에 999를 강제로 추가하고 세팅하던 기존의 예외 처리 조건문 줄을 제거했습니다.
        # 이제 DB에 있는 첫 번째 공종/호수 명칭이 자동으로 초기 선택됩니다.
        if self.comboHo.count() > 0:
            self.comboHo.setCurrentIndex(0)
                
        self.comboHo.blockSignals(False)

    def sync_items_by_discipline(self, discipline):
        """공종 변경 시 품명 리스트 재정렬"""
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
        # 새로 채워진 첫 번째 품명 기준으로 규격 및 재고 강제 호출
        self.handle_item_change(self.CB_Item.currentText())

    def handle_item_change(self, item_name):
        """품명이 바뀔 때 규격을 매칭하고 재고 현황판을 트리거합니다."""
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

    # =================================================================
    # 행 선택 시 하이라이트 시각 효과 로직
    # =================================================================
    def highlight_selected_row(self):
        for r in range(self.tableWidgetUse.rowCount()):
            bg_color = QColor(245, 247, 250) if (r % 4) in [2, 3] else QColor(255, 255, 255)
            for c in range(self.tableWidgetUse.columnCount()):
                item = self.tableWidgetUse.item(r, c)
                if item:
                    item.setBackground(bg_color)
                    
        current_row = self.tableWidgetUse.currentRow()
        if current_row >= 0:
            highlight_color = QColor(255, 224, 178) 
            for c in range(self.tableWidgetUse.columnCount()):
                item = self.tableWidgetUse.item(current_row, c)
                if item:
                    item.setBackground(highlight_color)

    # =================================================================
    # 저장 / 수정 / 삭제 비즈니스 로직
    # =================================================================
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
        
        # 재고 수량 초과 검증
        try:
            current_stock = database.get_current_stock(item_name, spec)
            if self.is_edit_mode:
                conn = database.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT qty FROM usage_ledger WHERE id = ?", (self.editing_row_id,))
                old_qty_res = cursor.fetchone()
                conn.close()
                if old_qty_res:
                    current_stock += old_qty_res[0]

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
                self.comboHo.addItem("999")
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
            
            # 고정 후 강제 재고 출력
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
        
        if self.comboDiscipline.count() > 0:
            self.comboDiscipline.setCurrentIndex(0)
            self.sync_items_by_discipline(self.comboDiscipline.currentText())
            
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
            
            if self.is_edit_mode:
                self.clear_usage_fields()
                
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