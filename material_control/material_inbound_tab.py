# material_inbound_tab.py

import sys
import os
import sqlite3
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor, QFont
import database
import pandas as pd # 최상단에 없다면 추가

class InboundTab(QWidget):
    def __init__(self, user_name="미인증"):
        super().__init__()
        self.current_user = user_name
        
        # 수정 모드 및 자동 계산 무한 루프 방지 플래그
        self.is_edit_mode = False
        self.editing_row_id = None  
        self.is_calculating = False  # 양방향 계산 오작동 방지용 플래그

        # 🌟 사진 저장을 위한 별도 디렉토리 설정 (DB 파일 위치 기준 또는 현재 실행 경로 기준)
        self.image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inbound_images")
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)

        # 개별 사진 경로를 임시 저장할 변수 리스트
        self.selected_photos = [None, None, None]

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

        # 🌟 [추가] 엑셀 다운로드 버튼 추가
        self.btn_export_excel = QPushButton("엑셀 내보내기 (Report)")
        self.btn_export_excel.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold; padding: 6px 12px;")
        self.btn_export_excel.clicked.connect(self.export_to_excel)
        top_bar.addWidget(self.btn_export_excel)
        
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
        #self.comboBoxInName.currentTextChanged.connect(self.sync_spec_combo)
        self.lineEditInQty.textChanged.connect(self.calculate_from_price)
        self.lineEditInPrice.textChanged.connect(self.calculate_from_price)
        self.lineEditInTotalPrice.textChanged.connect(self.calculate_from_total_price)

        # 콤보박스 비어있을 때 보일 안내 문구(Placeholder) 세팅
        self.comboBoxInDiscipline.setPlaceholderText("공종 입력 또는 선택")
        self.comboBoxInName.setPlaceholderText("품명 입력 또는 선택")
        self.comboBoxInSpec.setPlaceholderText("신규 추가 품목") # 👈 요청하신 희미한 글씨 처리

        # 시그널 연결 (계층형 필터링을 위해 공종 변경 시그널 추가)
        self.comboBoxInDiscipline.currentTextChanged.connect(self.filter_name_combo)
        self.comboBoxInName.currentTextChanged.connect(self.filter_spec_combo)
        
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
        """[단계 1] 최초 로드 시 공종(Discipline) 목록을 먼저 채우고 첫 항목을 강제 선택합니다."""
        self.comboBoxInDiscipline.blockSignals(True)
        self.comboBoxInDiscipline.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # 모든 공종 로드
        cursor.execute("""
            SELECT DISTINCT discipline FROM inbound_ledger 
            WHERE discipline IS NOT NULL AND discipline != '' 
            ORDER BY discipline ASC
        """)
        disciplines = cursor.fetchall()
        
        for d in disciplines:
            self.comboBoxInDiscipline.addItem(str(d[0]))
            
        # 마지막 입력 상태 복원 로직용 조회
        cursor.execute("""
            SELECT discipline, item_name, spec 
            FROM inbound_ledger 
            ORDER BY id DESC LIMIT 1
        """)
        last_entry = cursor.fetchone()
        conn.close()
        
        self.comboBoxInDiscipline.blockSignals(False)
        
        # 기존 저장 이력이 있다면 복원, 없다면 첫 번째 항목들로 자동 세팅
        if last_entry and not self.is_edit_mode:
            default_discipline = str(last_entry[0]) if last_entry[0] else ""
            default_item_name = str(last_entry[1]) if last_entry[1] else ""
            default_spec = str(last_entry[2]) if last_entry[2] else ""
            
            self.comboBoxInDiscipline.setEditText(default_discipline)
            self.filter_name_combo(default_discipline)
            self.comboBoxInName.setEditText(default_item_name)
            self.filter_spec_combo(default_item_name)
            self.comboBoxInSpec.setEditText(default_spec)
        else:
            if not self.is_edit_mode:
                # 등록된 공종이 있다면 첫 번째 공종을 선택시켜 연쇄 반응 유도
                if self.comboBoxInDiscipline.count() > 0:
                    self.comboBoxInDiscipline.setCurrentIndex(0)
                    self.filter_name_combo(self.comboBoxInDiscipline.currentText())
                else:
                    self.comboBoxInDiscipline.clearEditText()
                    self.comboBoxInName.clear()
                    self.comboBoxInName.clearEditText()
                    self.comboBoxInSpec.clear()
                    self.comboBoxInSpec.clearEditText()

    def filter_name_combo(self, discipline):
        """[단계 2] 공종이 바뀌면 기존 품명을 완전히 지우고, 새로운 품명 목록의 '첫 번째 항목'을 자동 선택합니다."""
        self.comboBoxInName.blockSignals(True)
        self.comboBoxInName.clear() # 👈 기존에 남아있던 품목 리스트와 텍스트를 완전히 리셋
        
        if not discipline.strip():
            self.comboBoxInName.blockSignals(False)
            self.filter_spec_combo("")
            return

        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # 선택된 공종에 맞는 품명 조회
        cursor.execute("""
            SELECT DISTINCT item_name FROM inbound_ledger 
            WHERE discipline = %s AND item_name IS NOT NULL AND item_name != ''
            ORDER BY item_name ASC
        """, (discipline.strip(),))
        items = cursor.fetchall()
        
        # 이력이 없다면 전체 마스터 로드
        if not items:
            cursor.execute("SELECT DISTINCT item_name FROM material_items ORDER BY item_name ASC")
            items = cursor.fetchall()
            
        conn.close()
        
        for i in items:
            self.comboBoxInName.addItem(str(i[0]))
            
        self.comboBoxInName.blockSignals(False)
        
        # 🌟 핵심: 리스트가 채워졌다면 첫 번째 품목을 자동으로 띄워줍니다.
        if self.comboBoxInName.count() > 0:
            self.comboBoxInName.setCurrentIndex(0)
        else:
            self.comboBoxInName.clearEditText()
            
        # 새로 선택된 품명에 맞춰 규격 콤보박스도 즉시 동기화
        self.filter_spec_combo(self.comboBoxInName.currentText())

    def filter_spec_combo(self, item_name):
        """[단계 3] 품명이 바뀌면 기존 규격을 지우고, 규격이 있으면 첫 항목 자동 선택 / 없으면 신규 추가 품목 문구를 띄웁니다."""
        self.comboBoxInSpec.blockSignals(True)
        self.comboBoxInSpec.clear() # 👈 기존 규격을 완전히 리셋
        
        discipline = self.comboBoxInDiscipline.currentText().strip()
        item_name = item_name.strip()
        
        if not item_name:
            self.comboBoxInSpec.blockSignals(False)
            self.comboBoxInSpec.clearEditText()
            return

        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # 공종 + 품명 조합으로 규격 조회
        cursor.execute("""
            SELECT DISTINCT spec FROM inbound_ledger 
            WHERE discipline = %s AND item_name = %s AND spec IS NOT NULL AND spec != ''
            ORDER BY spec ASC
        """, (discipline, item_name))
        specs = cursor.fetchall()
        
        if not specs:
            cursor.execute("""
                SELECT DISTINCT spec FROM material_items 
                WHERE item_name = %s AND spec IS NOT NULL AND spec != ''
                ORDER BY spec ASC
            """, (item_name,))
            specs = cursor.fetchall()
            
        conn.close()
        
        for s in specs:
            self.comboBoxInSpec.addItem(str(s[0]))
            
        self.comboBoxInSpec.blockSignals(False)
        
        # 🌟 핵심: 규격 리스트가 존재하면 첫 번째 규격을 바로 보여주고, 
        # 리스트가 비어있다면 빈칸으로 만들어 "신규 추가 품목" 희미한 글씨(Placeholder)가 나오게 합니다.
        if self.comboBoxInSpec.count() > 0:
            self.comboBoxInSpec.setCurrentIndex(0)
        else:
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

    # 🌟 고유 ID 조건 기반의 안전한 내역 삭제 및 물리 파일 제거 로직 (누락 복원 및 업그레이드)
    def delete_selected_row(self):
        current_row = self.tableWidgetInIn.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "삭제 오류", "삭제할 항목을 선택해 주세요.")
            return
            
        if QMessageBox.question(self, '확인', '선택한 내역을 삭제하시겠습니까?', QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            row_id = self.tableWidgetInIn.item(current_row, 0).data(Qt.UserRole + 1)
            
            # 물리 삭제용 타겟 리스트 생성
            photos_to_delete = []
            for i in range(3):
                p_name = self.tableWidgetInIn.item(current_row, 8 + i).data(Qt.UserRole)
                if p_name: 
                    photos_to_delete.append(p_name)
            
            try:
                conn = database.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM inbound_ledger WHERE id=%s", (row_id,))
                conn.commit()
                conn.close()
                
                # 이미지 저장소 파일 삭제 처리
                for p_name in photos_to_delete:
                    target_file = os.path.join(self.image_dir, p_name)
                    if os.path.exists(target_file):
                        os.remove(target_file)
                
                QMessageBox.information(self, "삭제 완료", "데이터와 연결된 현장 사진이 안전하게 파기되었습니다.")
                self.clear_inputs()
                self.table_display_in()
                
            except Exception as e:
                QMessageBox.critical(self, "삭제 실패", f"데이터베이스 삭제 중 에러 발생:\n{e}")

    def export_to_excel(self):
        """현재 테이블에 조회된 입고 현황을 엑셀 파일로 추출합니다."""
        row_count = self.tableWidgetInIn.rowCount()
        column_count = self.tableWidgetInIn.columnCount()
        
        if row_count == 0:
            QMessageBox.warning(self, "추출 실패", "엑셀로 내보낼 데이터가 없습니다.")
            return
            
        # 1. 엑셀 파일 저장 경로 선택창 띄우기
        default_filename = f"자재입고현황_레포트.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "엑셀 파일 저장", default_filename, "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return # 취소 시 리턴

        try:
            # 2. QTableWidget에서 헤더(컬럼명) 가져오기
            headers = []
            for col in range(column_count):
                headers.append(self.tableWidgetInIn.horizontalHeaderItem(col).text())
                
            # 3. 테이블 내부 데이터 추출하기
            table_data = []
            for row in range(row_count):
                row_data = []
                for col in range(column_count):
                    item = self.tableWidgetInIn.item(row, col)
                    val = item.text() if item else ""
                    # 수량, 단가, 총금액의 콤마(,) 제거 후 숫자로 변환하여 저장 (엑셀 수식 계산 연동 위함)
                    if col in [4, 5, 6]:
                        val = val.replace(",", "")
                        val = int(val) if val.isdigit() else 0
                    row_data.append(val)
                table_data.append(row_data)
                
            # 4. Pandas DataFrame 생성 및 엑셀 저장
            df = pd.DataFrame(table_data, columns=headers)
            
            # 엑셀 엔진을 활용해 서식(Style)을 조금 더 깔끔하게 인쇄용으로 지정 가능
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name="입고내역_Report")
                
                # [선택] openpyxl 서식 지정 (셀 너비 자동 최적화)
                workbook = writer.book
                worksheet = writer.sheets["입고내역_Report"]
                for col in worksheet.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    col_letter = col[0].column_letter
                    worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

            QMessageBox.information(self, "추출 완료", f"성공적으로 엑셀 레포트가 생성되었습니다.\n경로: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "시스템 에러", f"엑셀 변환 중 오류가 발생했습니다:\n{e}")