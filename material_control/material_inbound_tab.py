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
        
        # [추가] 수정 모드를 추적하기 위한 상태 변수들
        self.is_edit_mode = False
        self.editing_row_id = None  # DB의 고유 ID(rowid)를 추적

        self.init_ui()
        self.refresh_all_combos() # 콤보박스 전체 초기 로드
        self.table_display_in()

    def init_ui(self):
        main_layout = QHBoxLayout(self) # 현재 위젯(self)의 메인 레이아웃이 됩니다.
        
        # 주석 레이블에 사용할 소형 폰트 스타일
        notice_font = QFont()
        notice_font.setPointSize(9)
        notice_font.setItalic(True)
        notice_style = "color: #556677; margin-bottom: 5px; margin-left: 2px;"
        
        # =================================================================
        # 1. 좌측 영역: 입력 폼
        # =================================================================
        left_layout = QVBoxLayout()
        
        # [변경] 수정 상태일 때 그룹박스 타이틀이 동적으로 바뀌도록 인스턴스 변수화
        self.group_box_in = QGroupBox("자재 입고(등록) 입력")
        grid_in = QGridLayout()
        self.group_box_in.setLayout(grid_in)
        
        # (1) 입고 일자
        grid_in.addWidget(QLabel("입고일자:"), 0, 0)
        self.dateEditIn = QDateEdit()
        self.dateEditIn.setCalendarPopup(True)
        self.dateEditIn.setDate(QDate.currentDate())
        grid_in.addWidget(self.dateEditIn, 0, 1)
        
        # (2) 품명 (직접 입력 가능 콤보박스)
        grid_in.addWidget(QLabel("품명:"), 1, 0)
        self.comboBoxInName = QComboBox()
        self.comboBoxInName.setEditable(True)  # 직접 입력 가능
        grid_in.addWidget(self.comboBoxInName, 1, 1)
        
        # (3) 규격 (직접 입력 가능 콤보박스)
        grid_in.addWidget(QLabel("규격:"), 2, 0)
        self.comboBoxInSpec = QComboBox()
        self.comboBoxInSpec.setEditable(True)  # 직접 입력 가능
        grid_in.addWidget(self.comboBoxInSpec, 2, 1)
        
        # (4) 입고 수량
        grid_in.addWidget(QLabel("입고수량:"), 3, 0)
        self.lineEditInQty = QLineEdit()
        grid_in.addWidget(self.lineEditInQty, 3, 1)
        
        # (5) 단가
        grid_in.addWidget(QLabel("단가:"), 4, 0)
        self.lineEditInPrice = QLineEdit()
        grid_in.addWidget(self.lineEditInPrice, 4, 1)
        
        # (6) 공급처
        grid_in.addWidget(QLabel("공급처:"), 5, 0)
        self.lineEditInSupplier = QLineEdit()
        grid_in.addWidget(self.lineEditInSupplier, 5, 1)
        
        # (7) 비고
        grid_in.addWidget(QLabel("비고:"), 6, 0)
        self.lineEditInRemarks = QLineEdit()
        grid_in.addWidget(self.lineEditInRemarks, 6, 1)
        
        # (8) 등록 / 수정 처리 버튼 영역
        button_layout = QHBoxLayout()
        self.btn_save_in = QPushButton("입고 내역 등록")
        self.btn_save_in.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 35px;")
        self.btn_save_in.clicked.connect(self.process_inbound_save)
        button_layout.addWidget(self.btn_save_in)
        
        # [추가] 수정 취소 버튼 (수정 모드일 때만 활성화)
        self.btn_cancel_edit = QPushButton("수정 취소")
        self.btn_cancel_edit.setStyleSheet("background-color: #757575; color: white; font-weight: bold; height: 35px;")
        self.btn_cancel_edit.setVisible(False)
        self.btn_cancel_edit.clicked.connect(self.clear_input_fields)
        button_layout.addWidget(self.btn_cancel_edit)
        
        grid_in.addLayout(button_layout, 7, 0, 1, 2)
        
        left_layout.addWidget(self.group_box_in)
        left_layout.addStretch()
        
        # =================================================================
        # 2. 우측 영역: 테이블 및 관리 버튼
        # =================================================================
        right_layout = QVBoxLayout()
        
        # 상단 기능 제어 버튼군
        top_bar = QHBoxLayout()
        
        # [추가] 선택 내역 수정 버튼
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
        
        # 입고 원장 내역 테이블
        self.tableWidgetInIn = QTableWidget()
        self.tableWidgetInIn.setColumnCount(9)
        self.tableWidgetInIn.setHorizontalHeaderLabels(["입고일자", "품명", "규격", "수량", "단가", "총금액", "공급처", "비고", "입력자"])
        self.tableWidgetInIn.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidgetInIn.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.tableWidgetInIn)
        
        # 두 영역을 메인 레이아웃에 배치 (비율 좌1 : 우3)
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)

        # 콤보박스 변경 시 연쇄 동기화 시그널 연결
        self.comboBoxInName.currentTextChanged.connect(self.sync_spec_combo)

    # =================================================================
    # 데이터 흐름 제어 및 단계별 유효성 검증 함수
    # =================================================================
    def process_inbound_save(self):
        """새로 등록하거나 수정한 데이터를 안전한 단계를 거쳐 DB에 저장합니다."""
        item_name = self.comboBoxInName.currentText().strip()
        spec = self.comboBoxInSpec.currentText().strip()
        qty_str = self.lineEditInQty.text().strip()
        price_str = self.lineEditInPrice.text().strip()
        
        # 필수 입력 기본 검증
        if not item_name:
            QMessageBox.warning(self, "입력 오류", "품명을 선택하거나 입력해 주세요.")
            return
        if not qty_str or not qty_str.isdigit():
            QMessageBox.warning(self, "입력 오류", "정확한 입고 수량을 숫자로 입력해 주세요.")
            return

        # ----------------------------------------------------
        # [요구사항 반영] 단계별 신규 품명 / 규격 제어 흐름
        # ----------------------------------------------------
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # DB에 존재하는 품명인지 검사
        cursor.execute("SELECT COUNT(*) FROM material_items WHERE item_name = ?", (item_name,))
        item_exists = cursor.fetchone()[0] > 0
        
        # 1단계: 완전히 새로운 품명인 경우 처리
        if not item_exists:
            # 규격이 아직 입력되지 않았거나 공백이라면 안내 후 포커싱 이동
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

        # DB에 품명과 규격의 쌍이 일치하여 존재하는지 검사
        cursor.execute("SELECT COUNT(*) FROM material_items WHERE item_name = ? AND spec = ?", (item_name, spec))
        pair_exists = cursor.fetchone()[0] > 0
        
        # 2단계: 품명은 있거나 없더라도, '품명 + 규격' 조합이 아예 새롭다면 마스터 등록 최종 확인 창 띄우기
        if not pair_exists:
            reply = QMessageBox.question(
                self,
                "신규 자재 등록 확인",
                f"시스템 마스터에 없는 새로운 자재 정보입니다.\n\n"
                f"▶ 품명: {item_name}\n"
                f"▶ 규격: {spec}\n\n"
                f"위 정보가 정확합니까? 확인 후 등록됩니다.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                conn.close()
                return
            
            # 승인(Yes) 시 마스터 테이블(material_items)에 선 등록 처리
            try:
                cursor.execute("INSERT INTO material_items (item_name, spec) VALUES (?, ?)", (item_name, spec))
                conn.commit()
            except sqlite3.IntegrityError:
                pass # 동시성 예외 방지

        conn.close()
        # ----------------------------------------------------

        # 금액 수치 변환 계산
        qty = int(qty_str)
        unit_price = int(price_str) if price_str.isdigit() else 0
        total_price = qty * unit_price
        
        supplier = self.lineEditInSupplier.text().strip()
        remarks = self.lineEditInRemarks.text().strip()
        in_date = self.dateEditIn.date().toString("yyyy-MM-dd")
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        if self.is_edit_mode:
            # [수정 모드]: 기존 레코드를 업데이트
            cursor.execute("""
                UPDATE inbound_ledger
                SET in_date=?, item_name=?, spec=?, qty=?, unit_price=?, total_price=?, supplier=?, remarks=?, worker=?
                WHERE id = ?
            """, (in_date, item_name, spec, qty, unit_price, total_price, supplier, remarks, self.current_user, self.editing_row_id))
            conn.commit()
            QMessageBox.information(self, "수정 완료", "자재 입고 내역이 정상적으로 수정되었습니다.")
        else:
            # [일반 등록 모드]: 새로운 레코드 삽입
            cursor.execute("""
                INSERT INTO inbound_ledger (in_date, item_name, spec, qty, unit_price, total_price, supplier, remarks, worker)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (in_date, item_name, spec, qty, unit_price, total_price, supplier, remarks, self.current_user))
            conn.commit()
            QMessageBox.information(self, "등록 완료", "입고 내역이 등록되었습니다.")
            
        conn.close()
        
        # 입력창 정리 및 테이블/콤보 새로고침
        self.clear_input_fields()
        self.refresh_all_combos()
        self.table_display_in()

    # =================================================================
    # [기능 추가] 수정 연동 제어 함수군
    # =================================================================
    def load_selected_row_to_form(self):
        """테이블에서 선택한 행의 데이터를 왼쪽 입력 양식으로 다시 로드하여 수정 준비를 합니다."""
        current_row = self.tableWidgetInIn.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "선택 오류", "수정할 입고 내역 행을 테이블에서 선택해 주세요.")
            return
            
        # 선택된 행의 셀 문자열 추출
        in_date_str = self.tableWidgetInIn.item(current_row, 0).text()
        item_name = self.tableWidgetInIn.item(current_row, 1).text()
        spec = self.tableWidgetInIn.item(current_row, 2).text()
        qty = self.tableWidgetInIn.item(current_row, 3).text().replace(",", "")
        unit_price = self.tableWidgetInIn.item(current_row, 4).text().replace(",", "")
        supplier = self.tableWidgetInIn.item(current_row, 6).text()
        remarks = self.tableWidgetInIn.item(current_row, 7).text()
        
        # DB에서 고유 ID(id/rowid)를 역 추적하여 정확한 대상을 고정합니다.
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM inbound_ledger 
            WHERE in_date=? AND item_name=? AND spec=? AND qty=? AND supplier=?
            ORDER BY id DESC LIMIT 1
        """, (in_date_str, item_name, spec, int(qty), supplier))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            self.is_edit_mode = True
            self.editing_row_id = result[0]
            
            # 왼쪽 폼에 기존 값 세팅
            self.dateEditIn.setDate(QDate.fromString(in_date_str, "yyyy-MM-dd"))
            self.comboBoxInName.setEditText(item_name)
            self.comboBoxInSpec.setEditText(spec)
            self.lineEditInQty.setText(qty)
            self.lineEditInPrice.setText(unit_price)
            self.lineEditInSupplier.setText(supplier)
            self.lineEditInRemarks.setText(remarks)
            
            # UI 시각적 상태 업데이트 (수정 중임을 명시)
            self.group_box_in.setTitle("⚠️ 자재 입고 내역 수정 중")
            self.btn_save_in.setText("수정 완료 저장")
            self.btn_save_in.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; height: 35px;")
            self.btn_cancel_edit.setVisible(True)

    def clear_input_fields(self):
        """입력 창을 초기 상태로 비우고 일반 등록 모드로 되돌립니다."""
        self.is_edit_mode = False
        self.editing_row_id = None
        
        self.dateEditIn.setDate(QDate.currentDate())
        self.comboBoxInName.clearEditText()
        self.comboBoxInSpec.clearEditText()
        self.lineEditInQty.clear()
        self.lineEditInPrice.clear()
        self.lineEditInSupplier.clear()
        self.lineEditInRemarks.clear()
        
        # UI 스타일을 일반 등록 형태로 복구
        self.group_box_in.setTitle("자재 입고(등록) 입력")
        self.btn_save_in.setText("입고 내역 등록")
        self.btn_save_in.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 35px;")
        self.btn_cancel_edit.setVisible(False)

    # =================================================================
    # 기존 원본 콤보박스 및 테이블 조회 로직 유지 보완
    # =================================================================
    def refresh_all_combos(self):
        """DB 마스터 테이블에서 품명 리스트를 가져와 채웁니다."""
        self.comboBoxInName.blockSignals(True)
        self.comboBoxInName.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT item_name FROM material_items ORDER BY item_name ASC")
        items = cursor.fetchall()
        conn.close()
        
        for i in items:
            self.comboBoxInName.addItem(str(i[0]))
            
        self.comboBoxInName.blockSignals(False)
        self.comboBoxInName.clearEditText()
        self.comboBoxInSpec.clear()

    def sync_spec_combo(self, item_name):
        """선택된 품명에 속한 규격 리스트를 동적으로 필터링해 우측 규격 콤보에 연결합니다."""
        if not item_name:
            return
        self.comboBoxInSpec.blockSignals(True)
        self.comboBoxInSpec.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT spec FROM material_items WHERE item_name = ? ORDER BY spec ASC", (item_name,))
        specs = cursor.fetchall()
        conn.close()
        
        for s in specs:
            self.comboBoxInSpec.addItem(str(s[0]))
            
        self.comboBoxInSpec.blockSignals(False)
        # 만약 수정 모드인 경우 덮어씌워진 값이 유지되도록 clearEditText 처리를 분기합니다.
        if not self.is_edit_mode:
            self.comboBoxInSpec.clearEditText()

    def table_display_in(self):
        """테이블에 전체 입고 원장을 불러와 보기 좋게 디스플레이합니다."""
        self.tableWidgetInIn.setRowCount(0)
        self.tableWidgetInIn.setSortingEnabled(False)
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT in_date, item_name, spec, qty, unit_price, total_price, supplier, remarks, worker 
            FROM inbound_ledger 
            ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        for row_idx, row_data in enumerate(rows):
            self.tableWidgetInIn.insertRow(row_idx)
            bg_color = QColor(245, 247, 250) if (row_idx % 4) in [2, 3] else QColor(255, 255, 255)
            
            for col_idx, value in enumerate(row_data):
                if col_idx in [3, 4, 5]: # 수량, 단가, 총금액 포맷 처리
                    formatted_val = f"{value:,}" if isinstance(value, (int, float)) else str(value)
                    item = QTableWidgetItem(formatted_val)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                
                item.setBackground(bg_color)
                self.tableWidgetInIn.setItem(row_idx, col_idx, item)
                
        self.tableWidgetInIn.setSortingEnabled(True)
        self.tableWidgetInIn.resizeColumnsToContents()
        for col in range(self.tableWidgetInIn.columnCount()):
            current_width = self.tableWidgetInIn.columnWidth(col)
            self.tableWidgetInIn.setColumnWidth(col, current_width + 25)

    def delete_selected_row(self):
        """선택된 내역을 원장에서 지웁니다."""
        current_row = self.tableWidgetInIn.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "삭제 오류", "삭제할 항목을 선택해 주세요.")
            return
        if QMessageBox.question(self, '확인', '선택한 내역을 삭제하시겠습니까?', QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            in_date = self.tableWidgetInIn.item(current_row, 0).text()
            item_name = self.tableWidgetInIn.item(current_row, 1).text()
            spec = self.tableWidgetInIn.item(current_row, 2).text()
            qty = int(self.tableWidgetInIn.item(current_row, 3).text().replace(",", ""))
            
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM inbound_ledger 
                WHERE in_date=? AND item_name=? AND spec=? AND qty=?
            """, (in_date, item_name, spec, qty))
            conn.commit()
            conn.close()
            
            # 수정 중인 대상을 삭제해 버렸을 때를 대비해 초기화
            if self.is_edit_mode:
                self.clear_input_fields()
                
            self.table_display_in()
            QMessageBox.information(self, "성공", "선택한 내역이 삭제되었습니다.")