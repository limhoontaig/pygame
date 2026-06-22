# material_stock_tab.py
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QAbstractItemView,
    QGroupBox, QLabel, QComboBox, QDateEdit
)
from PyQt5.QtCore import Qt, QDate
import common.database as database  # 기존 데이터베이스 모듈 연동

class StockTab(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        
        # 1. UI 컴포넌트 생성 및 배치
        self.init_ui()
        
        # 2. 실시간 재고가 있는 '구분(Discipline)'들로 첫 번째 콤보박스 초기화
        self.init_discipline_combobox()
        
        # 3. 최초 데이터 로드
        self.load_stock_data()
        
        # 💡 중요: 초기화 완료 후 이벤트를 연결하여 무한 루프 및 중복 호출 방지
        self.connect_filter_events()

    def init_ui(self):
        """UI 레이아웃 설정 및 컴포넌트 초기화"""
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(12)

        # ==================================================
        # [좌측 영역] 검색바 + 재고 테이블
        # ==================================================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # 상단 실시간 텍스트 검색바
        top_layout = QHBoxLayout()
        self.LE_searchItem = QLineEdit()
        self.LE_searchItem.setPlaceholderText("결과 내 품명/규격 실시간 검색...")
        self.LE_searchItem.setClearButtonEnabled(True)
        self.LE_searchItem.setFixedHeight(30)
        self.LE_searchItem.textChanged.connect(self.filter_stock_data)
        top_layout.addWidget(self.LE_searchItem)
        
        self.PB_refreshStock = QPushButton("새로고침")
        self.PB_refreshStock.setFixedWidth(80)
        self.PB_refreshStock.setFixedHeight(30)
        self.PB_refreshStock.clicked.connect(self.refresh_all) 
        top_layout.addWidget(self.PB_refreshStock)
        left_layout.addLayout(top_layout)

        # 재고 테이블 설정 (여백 및 너비 최적화)
        self.tableWidgetStock = QTableWidget()
        self.tableWidgetStock.setColumnCount(4)
        self.tableWidgetStock.setHorizontalHeaderLabels(["구분", "품목명", "규격", "현재 재고량"])
        self.tableWidgetStock.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidgetStock.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidgetStock.setAlternatingRowColors(True)
        
        header = self.tableWidgetStock.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(1, QHeaderView.Interactive)      
        header.setSectionResizeMode(2, QHeaderView.Interactive)      
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) 
        
        self.tableWidgetStock.setColumnWidth(1, 180) 
        self.tableWidgetStock.setColumnWidth(2, 150) 
        
        left_layout.addWidget(self.tableWidgetStock)
        outer_layout.addWidget(left_widget, stretch=7)

        # ==================================================
        # [우측 영역] 상세 조회 조건 필터 패널
        # ==================================================
        filter_group = QGroupBox("조회 조건")
        filter_group.setFixedWidth(220) 
        filter_layout = QVBoxLayout(filter_group)
        filter_layout.setContentsMargins(12, 20, 12, 12)
        filter_layout.setSpacing(12)

        # 1. 조회기준일
        filter_layout.addWidget(QLabel("📅 조회기준일"))
        self.DE_baseDate = QDateEdit()
        self.DE_baseDate.setCalendarPopup(True)
        self.DE_baseDate.setDate(QDate.currentDate()) 
        self.DE_baseDate.setFixedHeight(28)
        filter_layout.addWidget(self.DE_baseDate)

        # 2. 조회 구분 (Discipline) 콤보박스 🌟 [추가]
        filter_layout.addWidget(QLabel("🗂️ 조회 구분 (분야별)"))
        self.CB_disciplineFilter = QComboBox()
        self.CB_disciplineFilter.setFixedHeight(28)
        filter_layout.addWidget(self.CB_disciplineFilter)

        # 3. 조회 품목 콤보박스
        filter_layout.addWidget(QLabel("📦 조회 품목 (재고 보유)"))
        self.CB_itemFilter = QComboBox()
        self.CB_itemFilter.setFixedHeight(28)
        filter_layout.addWidget(self.CB_itemFilter)

        # 4. 품목 규격 콤보박스
        filter_layout.addWidget(QLabel("📐 품목 규격 (선택 품목 기준)"))
        self.CB_specFilter = QComboBox()
        self.CB_specFilter.setFixedHeight(28)
        filter_layout.addWidget(self.CB_specFilter)

        filter_layout.addStretch() 

        # 하단 버튼 구역 (필터 초기화 버튼을 왼쪽에 배치)
        btn_layout = QHBoxLayout()
        self.PB_resetFilter = QPushButton("필터 초기화")
        self.PB_resetFilter.setFixedHeight(30)
        self.PB_resetFilter.clicked.connect(self.reset_filters)
        btn_layout.addWidget(self.PB_resetFilter)
        btn_layout.addStretch() 
        
        filter_layout.addLayout(btn_layout)
        outer_layout.addWidget(filter_group, stretch=3)

    def connect_filter_events(self):
        """이벤트 연결 (구분 -> 품목 -> 규격 순으로 체인 갱신 유도)"""
        self.CB_disciplineFilter.currentTextChanged.connect(self.on_discipline_filter_changed)
        self.CB_itemFilter.currentTextChanged.connect(self.on_item_filter_changed)
        self.CB_specFilter.currentTextChanged.connect(self.load_stock_data)
        self.DE_baseDate.dateChanged.connect(self.load_stock_data)

    def disconnect_filter_events(self):
        """값 변경 시 원치 않는 연쇄 호출을 막기 위한 이벤트 해제 함수"""
        try:
            self.CB_disciplineFilter.currentTextChanged.disconnect(self.on_discipline_filter_changed)
            self.CB_itemFilter.currentTextChanged.disconnect(self.on_item_filter_changed)
            self.CB_specFilter.currentTextChanged.disconnect(self.load_stock_data)
            self.DE_baseDate.dateChanged.disconnect(self.load_stock_data)
        except TypeError:
            pass

    def init_discipline_combobox(self):
        """1단계: 실시간 '현재 재고량 > 0'인 고유 구분(discipline) 리스트 추출하여 채우기"""
        try:
            self.disconnect_filter_events()

            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT item_name, spec, discipline FROM inbound_ledger WHERE item_name IS NOT NULL")
            all_rows = cursor.fetchall()
            conn.close()

            valid_disciplines = set()
            for item_name, spec, discipline in all_rows:
                if database.get_current_stock(item_name, spec) > 0:
                    if discipline:
                        valid_disciplines.add(str(discipline))

            self.CB_disciplineFilter.clear()
            self.CB_disciplineFilter.addItem("All")
            self.CB_disciplineFilter.addItems(sorted(list(valid_disciplines)))

            # 구분 'All' 기준으로 하위 품목 리스트도 연쇄 생성
            self.update_item_combobox("All")

        except Exception as e:
            print(f"구분 콤보박스 초기화 오류: {e}")
        finally:
            self.connect_filter_events()

    def update_item_combobox(self, selected_discipline):
        """2단계: 선택된 구분에 속하고 재고가 남아있는 '품목'만 추출하여 갱신"""
        try:
            # 품목 변경 시 발생할 이벤트를 잠시 차단
            try: self.CB_itemFilter.currentTextChanged.disconnect(self.on_item_filter_changed)
            except TypeError: pass

            conn = database.get_db_connection()
            cursor = conn.cursor()

            if selected_discipline == "All":
                cursor.execute("SELECT DISTINCT item_name, spec FROM inbound_ledger WHERE item_name IS NOT NULL")
            else:
                cursor.execute("SELECT DISTINCT item_name, spec FROM inbound_ledger WHERE discipline = %s", (selected_discipline,))
            
            rows = cursor.fetchall()
            conn.close()

            valid_items = set()
            for item_name, spec in rows:
                if database.get_current_stock(item_name, spec) > 0:
                    valid_items.add(item_name)

            self.CB_itemFilter.clear()
            self.CB_itemFilter.addItem("All")
            self.CB_itemFilter.addItems(sorted(list(valid_items)))

            # 현재 지정된 품목("All")에 맞춰 규격 콤보박스도 업데이트
            self.update_spec_combobox(selected_discipline, "All")

        except Exception as e:
            print(f"품목 콤보박스 업데이트 오류: {e}")
        finally:
            self.CB_itemFilter.currentTextChanged.connect(self.on_item_filter_changed)

    def update_spec_combobox(self, selected_discipline, selected_item):
        """3단계: 선택된 구분 및 품목에 해당하며 재고가 있는 '규격'만 추출하여 갱신"""
        try:
            try: self.CB_specFilter.currentTextChanged.disconnect(self.load_stock_data)
            except TypeError: pass

            conn = database.get_db_connection()
            cursor = conn.cursor()

            # 조건에 따른 동적 쿼리 작성
            query = "SELECT DISTINCT item_name, spec FROM inbound_ledger WHERE item_name IS NOT NULL"
            params = []

            if selected_discipline != "All":
                query += " AND discipline = %s"
                params.append(selected_discipline)
            if selected_item != "All":
                query += " AND item_name = %s"
                params.append(selected_item)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            valid_specs = set()
            for item_name, spec in rows:
                if spec and database.get_current_stock(item_name, spec) > 0:
                    valid_specs.add(spec)

            self.CB_specFilter.clear()
            self.CB_specFilter.addItem("All")
            self.CB_specFilter.addItems(sorted(list(valid_specs)))

        except Exception as e:
            print(f"규격 콤보박스 업데이트 오류: {e}")
        finally:
            self.CB_specFilter.currentTextChanged.connect(self.load_stock_data)

    def on_discipline_filter_changed(self, selected_discipline):
        """구분 콤보박스 변경 시 호출되는 슬롯 함수"""
        if not selected_discipline:
            return
        # 상위 구분이 바뀌었으므로 하위 품목과 규격을 다시 로드함
        self.update_item_combobox(selected_discipline)
        self.load_stock_data()

    def on_item_filter_changed(self, selected_item):
        """품목 콤보박스 변경 시 호출되는 슬롯 함수"""
        if not selected_item:
            return
        discipline = self.CB_disciplineFilter.currentText()
        self.update_spec_combobox(discipline, selected_item)
        self.load_stock_data()

    def load_stock_data(self):
        """우측 모든 조건(구분, 품목, 규격)에 대응하여 테이블 데이터를 로드 (SQLite)"""
        try:
            discipline_filter = self.CB_disciplineFilter.currentText() if hasattr(self, 'CB_disciplineFilter') else "All"
            item_filter = self.CB_itemFilter.currentText() if hasattr(self, 'CB_itemFilter') else "All"
            spec_filter = self.CB_specFilter.currentText() if hasattr(self, 'CB_specFilter') else "All"
            
            if not discipline_filter or not item_filter or not spec_filter:
                return

            conn = database.get_db_connection()
            cursor = conn.cursor()
            
            query = "SELECT DISTINCT item_name, spec, discipline FROM inbound_ledger WHERE 1=1"
            params = []

            if discipline_filter != "All":
                query += " AND discipline = %s"
                params.append(discipline_filter)
            if item_filter != "All":
                query += " AND item_name = %s"
                params.append(item_filter)
            if spec_filter != "All":
                query += " AND spec = %s"
                params.append(spec_filter)
                
            query += " ORDER BY discipline ASC, item_name ASC, spec ASC"
            
            cursor.execute(query, params)
            items = cursor.fetchall()
            conn.close()
            
            self.tableWidgetStock.setRowCount(0)
            row_idx = 0
            
            for item_name, spec, discipline in items:
                current_qty = database.get_current_stock(item_name, spec)
                
                self.tableWidgetStock.insertRow(row_idx)
                
                item_discipline = QTableWidgetItem(str(discipline or ""))
                item_name_obj = QTableWidgetItem(str(item_name))
                item_spec = QTableWidgetItem(str(spec or ""))
                item_qty = QTableWidgetItem(f"{current_qty:,}")
                
                item_qty.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_discipline.setTextAlignment(Qt.AlignCenter)
                
                if current_qty <= 0:
                    item_qty.setForeground(Qt.red)
                
                self.tableWidgetStock.setItem(row_idx, 0, item_discipline)
                self.tableWidgetStock.setItem(row_idx, 1, item_name_obj)
                self.tableWidgetStock.setItem(row_idx, 2, item_spec)
                self.tableWidgetStock.setItem(row_idx, 3, item_qty)
                row_idx += 1
                
            self.filter_stock_data()
                
        except Exception as e:
            pass

    def filter_stock_data(self):
        """좌측 상단 텍스트 검색 결과에 따른 행 필터링"""
        search_text = self.LE_searchItem.text().strip().lower()
        
        for row in range(self.tableWidgetStock.rowCount()):
            name_item = self.tableWidgetStock.item(row, 1)
            spec_item = self.tableWidgetStock.item(row, 2)
            
            if name_item and spec_item:
                name_text = name_item.text().lower()
                spec_text = spec_item.text().lower()
                
                if search_text in name_text or search_text in spec_text:
                    self.tableWidgetStock.setRowHidden(row, False)
                else:
                    self.tableWidgetStock.setRowHidden(row, True)

    def reset_filters(self):
        """모든 필터 조건을 최초 상태인 'All'로 초기화"""
        self.disconnect_filter_events()
        self.CB_disciplineFilter.setCurrentIndex(0)
        self.update_item_combobox("All")
        self.DE_baseDate.setDate(QDate.currentDate())
        self.LE_searchItem.clear()
        self.connect_filter_events()
        self.load_stock_data()

    def refresh_all(self):
        """새로고침 시 전반적인 최상위 콤보박스 및 테이블 재생성"""
        self.init_discipline_combobox()
        self.load_stock_data()