# material_usage_tab.py

import sqlite3
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor, QFont
import database

class UsageTab(QWidget):
    def __init__(self, user_name):
        super().__init__()
        self.current_user = user_name
        self.init_ui()
        self.refresh_usage_data()
        # ----------------------------------------------------
        # [수정] 프로그램이 최초로 켜질 때 콤보박스를 실시간 재고 기준으로 세팅합니다.
        # ----------------------------------------------------
        self.load_initial_data()

    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # --- 좌측 입력 폼 ---
        left_layout = QVBoxLayout()
        group_box = QGroupBox("자재 사용(출고) 입력")
        grid = QGridLayout()
        group_box.setLayout(grid)

        # 날짜
        grid.addWidget(QLabel("사용일자:"), 0, 0)
        self.DE_OutDate = QDateEdit()
        self.DE_OutDate.setCalendarPopup(True)
        self.DE_OutDate.setDate(QDate.currentDate())
        grid.addWidget(self.DE_OutDate, 0, 1)

        # 구분 (공용/세대)
        grid.addWidget(QLabel("구분:"), 1, 0)
        self.CB_Category = QComboBox()
        self.CB_Category.addItems(["세대", "공용"])
        grid.addWidget(self.CB_Category, 1, 1)

        # 동호 선택 영역 (동/호 콤보박스)
        grid.addWidget(QLabel("동/호:"), 2, 0)
        dong_ho_layout = QHBoxLayout()
        self.CB_Dong = QComboBox()
        self.CB_Ho = QComboBox()
        dong_ho_layout.addWidget(self.CB_Dong)
        dong_ho_layout.addWidget(self.CB_Ho)
        grid.addLayout(dong_ho_layout, 2, 1)

        # 품명 및 규격 콤보박스
        grid.addWidget(QLabel("품명:"), 3, 0)
        self.CB_Item = QComboBox()
        grid.addWidget(self.CB_Item, 3, 1)

        grid.addWidget(QLabel("규격:"), 4, 0)
        self.CB_Spec = QComboBox()
        grid.addWidget(self.CB_Spec, 4, 1)

        # 현재 재고 표시 칸 (읽기 전용)
        grid.addWidget(QLabel("현재 재고:"), 5, 0)
        self.LE_CurrentStock = QLineEdit()
        self.LE_CurrentStock.setReadOnly(True)
        self.LE_CurrentStock.setStyleSheet("background-color: #EFEFEF; font-weight: bold; color: blue;")
        grid.addWidget(self.LE_CurrentStock, 5, 1)

        # 사용 수량
        grid.addWidget(QLabel("사용수량:"), 6, 0)
        self.LE_Qty = QLineEdit()
        grid.addWidget(self.LE_Qty, 6, 1)

        # 비고
        grid.addWidget(QLabel("비고:"), 7, 0)
        self.LE_Remarks = QLineEdit()
        grid.addWidget(self.LE_Remarks, 7, 1)

        # 등록 버튼
        self.btn_save = QPushButton("사용 내역 등록")
        self.btn_save.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; height: 35px;")
        self.btn_save.clicked.connect(self.save_usage)
        grid.addWidget(self.btn_save, 8, 0, 1, 2)

        left_layout.addWidget(group_box)
        left_layout.addStretch()
        layout.addLayout(left_layout, 1)

        # --- 우측 내역 테이블 (사용자 파일 기준 9칸 완벽 유지) ---
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["사용일자", "구분", "동", "호", "품명", "규격", "수량", "비고", "입력자"])
        layout.addWidget(self.table, 3)

        # ----------------------------------------------------
        # [중요] 시그널(이벤트) 연결 구조 수정 (안정적인 실시간 연동)
        # ----------------------------------------------------
        self.CB_Dong.currentTextChanged.connect(self.load_ho_list)
        self.CB_Item.currentTextChanged.connect(self.load_spec_list)
        self.CB_Spec.currentTextChanged.connect(self.update_stock_display)

    def load_initial_data(self):
        """동 목록 및 '재고가 있는' 품명 목록 초기 로드"""
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # 1. 동 목록 가져오기 및 숫자 정렬
        cursor.execute("SELECT DISTINCT dong FROM dongho_master")
        dongs = [row[0] for row in cursor.fetchall() if row[0]]
        try:
            dongs.sort(key=lambda x: int(''.join(filter(str.isdigit, str(x)))) if any(c.isdigit() for c in str(x)) else 9999)
        except Exception:
            dongs.sort()
            
        # 블로킹 처리: clear() 시 발생하는 이벤트 노이즈 방지
        self.CB_Dong.blockSignals(True)
        self.CB_Dong.clear()
        for d in dongs: 
            self.CB_Dong.addItem(str(d))
        self.CB_Dong.blockSignals(False)

        # 첫 번째 동에 맞는 호수 목록 강제 연쇄 호출
        if dongs:
            self.load_ho_list(self.CB_Dong.currentText())

        # 2. [재고 필터링] 총 입고량 - 총 출고량 > 0 인 품명만 조회
        cursor.execute("""
            SELECT DISTINCT m.item_name 
            FROM material_items m
            WHERE (
                (SELECT COALESCE(SUM(qty), 0) FROM inbound_ledger WHERE item_name = m.item_name) - 
                (SELECT COALESCE(SUM(qty), 0) FROM outbound_ledger WHERE item_name = m.item_name)
            ) > 0
            ORDER BY m.item_name ASC
        """)
        items = cursor.fetchall()
        
        self.CB_Item.blockSignals(True)
        self.CB_Item.clear()
        for i in items: 
            self.CB_Item.addItem(str(i[0]))
        self.CB_Item.blockSignals(False)
        
        conn.close()

        # [핵심 추가] 품명이 로드되면 자동으로 첫 번째 품명의 규격과 재고를 채우도록 연쇄 유도
        if items:
            self.load_spec_list(self.CB_Item.currentText())
        else:
            self.CB_Spec.clear()
            self.LE_CurrentStock.clear()

    def load_ho_list(self, dong):
        """선택된 동에 맞는 호수 목록 로드 (숫자 순 정렬)"""
        self.CB_Ho.clear()
        if not dong: 
            return
            
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT ho FROM dongho_master WHERE dong = ?", (dong,))
        hos = [row[0] for row in cursor.fetchall() if row[0]]
        
        try:
            hos.sort(key=lambda x: int(''.join(filter(str.isdigit, str(x)))) if any(c.isdigit() for c in str(x)) else 9999)
        except Exception:
            hos.sort()
            
        for h in hos: 
            self.CB_Ho.addItem(str(h))
            
        conn.close()

    def load_spec_list(self, item_name):
        """선택된 품명 중 '재고가 있는' 규격 목록만 로드"""
        self.CB_Spec.blockSignals(True)
        self.CB_Spec.clear()
        
        if not item_name:
            self.CB_Spec.blockSignals(False)
            self.LE_CurrentStock.clear()
            return
            
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # 해당 품명 중 (총 입고량 - 총 출고량) > 0 인 규격만 필터링 조회
        cursor.execute("""
            SELECT DISTINCT m.spec 
            FROM material_items m 
            WHERE m.item_name = ?
              AND (
                  (SELECT COALESCE(SUM(qty), 0) FROM inbound_ledger WHERE item_name = m.item_name AND spec = m.spec) - 
                  (SELECT COALESCE(SUM(qty), 0) FROM outbound_ledger WHERE item_name = m.item_name AND spec = m.spec)
              ) > 0
            ORDER BY m.spec ASC
        """, (item_name,))
        specs = cursor.fetchall()
        
        for s in specs:
            self.CB_Spec.addItem(str(s[0]))
        conn.close()
        self.CB_Spec.blockSignals(False)
        
        # 규격 로드가 끝나면 최종적으로 현재 재고 숫자 표기 반영
        self.update_stock_display()

    def update_stock_display(self):
        """현재 선택된 품명과 규격을 바탕으로 재고를 조회하여 표시"""
        item_name = self.CB_Item.currentText()
        spec = self.CB_Spec.currentText()
        
        if item_name and spec:
            stock = database.get_current_stock(item_name, spec)
            self.LE_CurrentStock.setText(f"{stock} 개")
        else:
            self.LE_CurrentStock.clear()

    def save_usage(self):
        """자재 사용 내역 저장 (재고 부족 검증 기능 완벽 연동)"""
        qty_str = self.LE_Qty.text().strip()
        if not qty_str:
            QMessageBox.warning(self, "입력 오류", "사용수량을 입력해 주세요.")
            return

        if not qty_str.isdigit():
            QMessageBox.warning(self, "입력 오류", "수량은 숫자만 입력 가능합니다.")
            return

        req_qty = int(qty_str)
        if req_qty <= 0:
            QMessageBox.warning(self, "입력 오류", "사용수량은 1개 이상이어야 합니다.")
            return

        item_name = self.CB_Item.currentText()
        spec = self.CB_Spec.currentText()
        
        if not item_name or not spec:
            QMessageBox.warning(self, "입력 오류", "품명과 규격을 선택해 주세요.")
            return

        # 실시간 DB 마이너스 재고 검증
        current_stock = database.get_current_stock(item_name, spec)
        if req_qty > current_stock:
            QMessageBox.critical(
                self, 
                "재고 부족", 
                f"재고가 부족하여 저장을 할 수 없습니다.\n\n"
                f"현재 재고: {current_stock} 개\n"
                f"요청 수량: {req_qty} 개"
            )
            return

        # 데이터 세이브 데이터셋 빌드 (9개 컬럼 매칭)
        data = (
            self.DE_OutDate.date().toString("yyyy-MM-dd"),
            self.CB_Dong.currentText(),
            self.CB_Ho.currentText(),
            self.CB_Category.currentText(),
            item_name,
            spec,
            req_qty,
            self.LE_Remarks.text(),
            self.current_user
        )

        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO outbound_ledger (out_date, dong, ho, category, item_name, spec, qty, remarks, worker)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        conn.close()
        
        # 화면 정리 및 리프레시
        self.LE_Qty.clear()
        self.LE_Remarks.clear()
        self.refresh_usage_data()
        
        # 사용 등록 완료로 인해 재고가 변했으므로 콤보박스 목록 다시 동기화
        self.load_initial_data()
        QMessageBox.information(self, "성공", "사용 내역이 등록되었습니다.")

    def refresh_usage_data(self):
        """테이블 새로고침 (2칸씩 색상 구분 포함 - 사용자 코드 원본 그대로)"""
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT out_date, category, dong, ho, item_name, spec, qty, remarks, worker FROM outbound_ledger ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()

        self.table.setRowCount(0)
        for r_idx, row_data in enumerate(rows):
            self.table.insertRow(r_idx)
            bg_color = QColor(245, 247, 250) if (r_idx % 4) in [2, 3] else QColor(255, 255, 255)
            
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                if col_idx == 6:  # 수량 우측 정렬
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignCenter)
                
                item.setBackground(bg_color)
                self.table.setItem(r_idx, col_idx, item)
                
        self.table.resizeColumnsToContents()

    def showEvent(self, event):
        """[추가] 다른 탭에 있다가 이 탭으로 클릭해서 들어올 때마다 실시간 목록 자동 갱신"""
        super().showEvent(event)
        self.load_initial_data()