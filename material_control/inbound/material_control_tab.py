# material_control_tab.py

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor  # 행 색상 변경을 위해 추가
import pygame.material_control.z_old_files.database as database

class MatWindow(QMainWindow):
    def __init__(self, user_name="미인증"):
        super().__init__()
        self.current_user = user_name
        self.setWindowTitle(f"강남데시앙파크 자재관리 시스템 - [접속자: {self.current_user}]")
        self.resize(1200, 750)
        
        self.init_ui()
        self.refresh_item_combo()
        self.table_display_in()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # =================================================================
        # 1. 좌측 영역: 입력 폼 + 신규 자재 추가 폼
        # =================================================================
        left_layout = QVBoxLayout()
        
        # [그룹 1] 기존 자재 입고 등록 폼
        group_input = QGroupBox("자재 입고 등록")
        grid_layout = QGridLayout()
        group_input.setLayout(grid_layout)
        
        grid_layout.addWidget(QLabel("입고일자:"), 0, 0)
        self.DE_InDate = QDateEdit()
        self.DE_InDate.setCalendarPopup(True)
        self.DE_InDate.setDate(QDate.currentDate())
        grid_layout.addWidget(self.DE_InDate, 0, 1)
        
        grid_layout.addWidget(QLabel("품명:"), 1, 0)
        self.CB_InItem = QComboBox()
        self.CB_InItem.currentTextChanged.connect(self.refresh_spec_combo)
        grid_layout.addWidget(self.CB_InItem, 1, 1)
        
        grid_layout.addWidget(QLabel("규격:"), 2, 0)
        self.CB_InSpec = QComboBox()
        grid_layout.addWidget(self.CB_InSpec, 2, 1)
        
        grid_layout.addWidget(QLabel("입고수량 (*필수):"), 3, 0)
        self.LE_InQty = QLineEdit()
        self.LE_InQty.textChanged.connect(self.calculate_unit_price)
        grid_layout.addWidget(self.LE_InQty, 3, 1)
        
        grid_layout.addWidget(QLabel("구입금액 (*필수):"), 4, 0)
        self.LE_InPrice = QLineEdit()
        self.LE_InPrice.textChanged.connect(self.calculate_unit_price)
        grid_layout.addWidget(self.LE_InPrice, 4, 1)
        
        grid_layout.addWidget(QLabel("단가:"), 5, 0)
        self.LE_InUnitPrice = QLineEdit()
        self.LE_InUnitPrice.setReadOnly(True)
        self.LE_InUnitPrice.setStyleSheet("background-color: #EEEEEE;")
        grid_layout.addWidget(self.LE_InUnitPrice, 5, 1)
        
        grid_layout.addWidget(QLabel("구입업체:"), 6, 0)
        self.LE_InSupplier = QLineEdit()
        grid_layout.addWidget(self.LE_InSupplier, 6, 1)
        
        grid_layout.addWidget(QLabel("비고:"), 7, 0)
        self.LE_InRemarks = QLineEdit()
        grid_layout.addWidget(self.LE_InRemarks, 7, 1)
        
        left_layout.addWidget(group_input)
        
        # 입고 등록 버튼
        self.PB_InInsert = QPushButton("자재 입고 등록")
        self.PB_InInsert.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; height: 35px;")
        self.PB_InInsert.clicked.connect(self.in_data_input)
        left_layout.addWidget(self.PB_InInsert)
        
        left_layout.addSpacing(15)
        
        # [그룹 2] 신규 기초 자재/규격 추가 폼
        group_new_material = QGroupBox("✨ 신규 자재/규격 마스터 추가")
        new_grid = QGridLayout()
        group_new_material.setLayout(new_grid)
        
        new_grid.addWidget(QLabel("새 품명:"), 0, 0)
        self.LE_NewItem = QLineEdit()
        self.LE_NewItem.setPlaceholderText("기존 품명 선택 시 비워둠")
        new_grid.addWidget(self.LE_NewItem, 0, 1)
        
        new_grid.addWidget(QLabel("새 규격:"), 1, 0)
        self.LE_NewSpec = QLineEdit()
        new_grid.addWidget(self.LE_NewSpec, 1, 1)
        
        left_layout.addWidget(group_new_material)
        
        # 마스터 등록 버튼
        self.PB_AddMaster = QPushButton("기초 자재 마스터에 추가")
        self.PB_AddMaster.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 30px;")
        self.PB_AddMaster.clicked.connect(self.add_new_material_master)
        left_layout.addWidget(self.PB_AddMaster)
        
        left_layout.addSpacing(10)
        
        # 내역 삭제 버튼
        self.PB_InDelete = QPushButton("선택된 입고 내역 삭제")
        self.PB_InDelete.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; height: 30px;")
        self.PB_InDelete.clicked.connect(self.delete_selected_row)
        left_layout.addWidget(self.PB_InDelete)
        
        left_layout.addStretch()
        
        # =================================================================
        # 2. 우측 영역: 대장 출력 테이블
        # =================================================================
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("▶ 입고 이력 현황 (최신순)"))
        
        self.tableWidgetInIn = QTableWidget()
        self.tableWidgetInIn.setColumnCount(9)
        self.tableWidgetInIn.setHorizontalHeaderLabels(['일자', '품명', '규격', '입고수량', '구입금액', '단가', '구입업체', '비고', '입력자'])
        self.tableWidgetInIn.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidgetInIn.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # ★ [추가] 헤더 클릭 시 자동으로 소트(정렬) 기능 활성화
        self.tableWidgetInIn.setSortingEnabled(True)

        # ★ [개선] 표 가독성 향상을 위한 설정 변경
        self.tableWidgetInIn.verticalHeader().setDefaultSectionSize(32) # 행 높이를 32픽셀로 늘려 시원하게 만듦
        
        # =================================================================
        # ★ [피드백 반영] 테이블 제목창(헤더) 디자인 강화 세팅
        # =================================================================
        # 1. 제목창 스타일 시트 적용: 은은한 네이비 블루 배경색 + 흰색 글자
        header_style = """
            QHeaderView::section {
                background-color: #3A4B64;     /* 깔끔하고 신뢰감을 주는 짙은 회청색 배경 */
                color: white;                  /* 글자색 흰색 */
                font-weight: bold;             /* 글자 볼드체 */
                font-size: 13pt;               /* ★ 기본 11pt에서 2포인트 키운 13pt */
                border: 1px solid #2C3A4E;     /* 헤더 칸막이 경계선 */
            }
        """
        self.tableWidgetInIn.horizontalHeader().setStyleSheet(header_style)
        
        # 2. 제목창의 높이를 아래 자재 목록 행 높이와 동일하게 32픽셀로 지정
        self.tableWidgetInIn.horizontalHeader().setFixedHeight(32)
        
        # 3. 제목창 글자가 잘리지 않도록 입체감 유지 설정
        self.tableWidgetInIn.horizontalHeader().setHighlightSections(False)
        # =================================================================
        
        right_layout.addWidget(self.tableWidgetInIn)
        
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 7)

    # =================================================================
    # ⚙️ 기능 및 이벤트 처리 함수부
    # =================================================================
    
    def refresh_item_combo(self):
        self.CB_InItem.blockSignals(True)
        self.CB_InItem.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT item_name FROM material_items ORDER BY item_name ASC")
        items = cursor.fetchall()
        conn.close()
        
        if items:
            for item in items:
                self.CB_InItem.addItem(item[0])
        self.CB_InItem.blockSignals(False)
        self.refresh_spec_combo(self.CB_InItem.currentText())

    def refresh_spec_combo(self, selected_item):
        self.CB_InSpec.clear()
        if not selected_item:
            return
            
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT spec FROM material_items WHERE item_name = ? ORDER BY spec ASC", (selected_item,))
        specs = cursor.fetchall()
        conn.close()
        
        for spec in specs:
            self.CB_InSpec.addItem(spec[0])

    def calculate_unit_price(self):
        try:
            qty = int(self.LE_InQty.text()) if self.LE_InQty.text() else 0
            price = int(self.LE_InPrice.text()) if self.LE_InPrice.text() else 0
            if qty > 0 and price > 0:
                self.LE_InUnitPrice.setText(str(int(price / qty)))
            else:
                self.LE_InUnitPrice.clear()
        except ValueError:
            self.LE_InUnitPrice.clear()

    def in_data_input(self):
        """ [등록] 필수 입력 유효성 검사 강화 버전 """
        in_date = self.DE_InDate.date().toString('yyyy-MM-dd')
        item_name = self.CB_InItem.currentText()
        spec = self.CB_InSpec.currentText()
        
        # 텍스트 가져오기 및 공백 제거
        str_qty = self.LE_InQty.text().strip()
        str_price = self.LE_InPrice.text().strip()
        
        # ★ [피드백 반영] 필수 항목 체크 오류 알림
        if not str_qty or not str_price:
            QMessageBox.warning(self, "입력 오류", "입고수량과 구입금액은 필수 입력 사항입니다.\n내용을 입력해 주세요.")
            return
            
        try:
            qty = int(str_qty)
            total_price = int(str_price)
            if qty <= 0 or total_price < 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "입고수량과 구입금액에는 올바른 숫자 값을 입력해 주세요.")
            return

        unit_price = int(self.LE_InUnitPrice.text()) if self.LE_InUnitPrice.text() else 0
        supplier = self.LE_InSupplier.text().strip() or '*'
        remarks = self.LE_InRemarks.text().strip() or '*'
        
        if not item_name or not spec:
            QMessageBox.warning(self, "입력 오류", "선택된 자재 품명 또는 규격이 없습니다.")
            return

        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO inbound_ledger (in_date, item_name, spec, qty, total_price, unit_price, supplier, remarks, worker)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (in_date, item_name, spec, qty, total_price, unit_price, supplier, remarks, self.current_user))
        conn.commit()
        conn.close()
        
        # 입력창 초기화
        self.LE_InQty.clear()
        self.LE_InPrice.clear()
        self.LE_InUnitPrice.clear()
        self.LE_InSupplier.clear()
        self.LE_InRemarks.clear()
        
        self.table_display_in()
        QMessageBox.information(self, "등록 완료", "입고 내역 기록이 데이터베이스에 저장되었습니다.")

    def table_display_in(self):
        """ DB에서 데이터를 실시간으로 읽어와 TableWidget에 매핑 (정렬 기능 호환 버전) """
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT in_date, item_name, spec, qty, total_price, unit_price, supplier, remarks, worker FROM inbound_ledger ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        
        # ★ [중요] 데이터를 새로 바인딩할 때는 잠시 정렬 기능을 꺼두어야 에러가 나지 않습니다.
        self.tableWidgetInIn.setSortingEnabled(False)
        
        self.tableWidgetInIn.setRowCount(0)
        
        for row_idx, row_data in enumerate(rows):
            self.tableWidgetInIn.insertRow(row_idx)
            
            if (row_idx % 4) in [2, 3]:
                bg_color = QColor(245, 247, 250)
            else:
                bg_color = QColor(255, 255, 255)
                
            for col_idx, value in enumerate(row_data):
                # 수량, 구입금액, 단가 (컬럼 인덱스 3, 4, 5번) 처리
                if col_idx in [3, 4, 5]:
                    # 숫자가 정렬될 때 문자열로 인식되지 않도록 QTableWidgetItem 생성 후 데이터 타입을 정수로 명시 세팅
                    item = QTableWidgetItem()
                    item.setData(Qt.DisplayRole, int(value) if value is not None else 0)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    # 일반 문자열 컬럼 (일자, 품명, 입력자 등)
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                    
                item.setBackground(bg_color)
                self.tableWidgetInIn.setItem(row_idx, col_idx, item)
                
        # ★ 데이터를 모두 채운 후 다시 정렬 기능을 켜줍니다.
        self.tableWidgetInIn.setSortingEnabled(True)
        
        # 간격 여유 조절
        self.tableWidgetInIn.resizeColumnsToContents()
        for col in range(self.tableWidgetInIn.columnCount()):
            current_width = self.tableWidgetInIn.columnWidth(col)
            self.tableWidgetInIn.setColumnWidth(col, current_width + 25)

    def add_new_material_master(self):
        """ [기초 자재 마스터에 추가] 버튼 연동 로직 (중복 에러 완벽 방지 버전) """
        new_item = self.LE_NewItem.text().strip()
        new_spec = self.LE_NewSpec.text().strip()
        
        # 만약 새 품명을 입력하지 않고 기존 콤보박스에서 선택된 상태에서 규격만 추가하고 싶을 때
        if not new_item and self.CB_InItem.currentText():
            new_item = self.CB_InItem.currentText()

        # 필수 입력 체크
        if not new_item or not new_spec:
            QMessageBox.warning(self, "입력 누락", "품명과 규격을 모두 입력해 주세요.")
            return
            
        conn = database.get_db_connection()
        cursor = conn.cursor()
        try:
            # DB에 신규 기초 자재 추가 시도
            cursor.execute("INSERT INTO material_items (item_name, spec) VALUES (?, ?)", (new_item, new_spec))
            conn.commit()
            
            # 성공 시 안내 메시지
            QMessageBox.information(self, "등록 완료", f"기초 자재가 마스터에 등록되었습니다.\n▶ [{new_item} - {new_spec}]")
            
            # 정상 등록 시에도 입력칸 초기화
            self.LE_NewItem.clear()
            self.LE_NewSpec.clear()
            
            # 콤보박스 실시간 새로고침 및 자동 선택
            self.refresh_item_combo()
            self.CB_InItem.setCurrentText(new_item)
            self.CB_InSpec.setCurrentText(new_spec)
            
        except sqlite3.IntegrityError:
            # ★ [핵심 피드백 반영] 중복 발생 시 프로그램이 죽지 않고 안내창을 띄웁니다.
            QMessageBox.warning(
                self, 
                "중복 등록 불가", 
                f"이미 자재 마스터에 등록되어 있는 자재입니다.\n\n재등록 하실 수 없으며, 입력 칸은 원래대로 초기화됩니다.\n▶ [{new_item} - {new_spec}]"
            )
            
            # ★ [핵심 피드백 반영] 중복 에러 발생 후 입력칸을 깨끗하게 원래대로 비워줍니다.
            self.LE_NewItem.clear()
            self.LE_NewSpec.clear()
            
        except Exception as e:
            # 혹시 모를 기타 시스템 에러 예외 처리
            QMessageBox.critical(self, "시스템 오류", f"데이터베이스 작업 중 오류가 발생했습니다:\n{str(e)}")
            
        finally:
            conn.close()

    def delete_selected_row(self):
        current_row = self.tableWidgetInIn.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "삭제 오류", "삭제할 항목을 선택해 주세요.")
            return
        if QMessageBox.question(self, '확인', '선택한 내역을 삭제하시겠습니까?', QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            in_date = self.tableWidgetInIn.item(current_row, 0).text()
            item_name = self.tableWidgetInIn.item(current_row, 1).text()
            spec = self.tableWidgetInIn.item(current_row, 2).text()
            
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM inbound_ledger 
                WHERE rowid = (SELECT rowid FROM inbound_ledger WHERE in_date=? AND item_name=? AND spec=? ORDER BY id DESC LIMIT 1)
            """, (in_date, item_name, spec))
            conn.commit()
            conn.close()
            self.table_display_in()