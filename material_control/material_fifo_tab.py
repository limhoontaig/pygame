# material_fifo_status_tab.py
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QDateEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QMessageBox, QComboBox
)
from PyQt5.QtCore import QDate, Qt
import database

class FifoStatusTab(QWidget):
    def __init__(self, current_user="미인증"):
        super().__init__()
        self.current_user = current_user
        self.init_ui()
        self.load_item_combobox()
        self.calculate_and_display_fifo()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # =================================================================
        # 1. 상단 조건 검색 및 기간 설정 영역
        # =================================================================
        search_group = QGroupBox("입출고 및 선입선출 현황 검색 조건")
        search_layout = QHBoxLayout(search_group)

        # 품목 선택 필터
        search_layout.addWidget(QLabel("품목 선택:"))
        self.combo_item_filter = QComboBox()
        self.combo_item_filter.setMinimumWidth(250)
        self.combo_item_filter.currentIndexChanged.connect(self.calculate_and_display_fifo)
        search_layout.addWidget(self.combo_item_filter)

        search_layout.addSpacing(20)

        # 기간 설정 필터
        search_layout.addWidget(QLabel("조회 기간:"))
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        # 기본값: 이번 달 1일
        current_date = QDate.currentDate()
        self.date_start.setDate(QDate(current_date.year(), current_date.month(), 1))
        search_layout.addWidget(self.date_start)

        search_layout.addWidget(QLabel("~"))

        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(current_date)
        search_layout.addWidget(self.date_end)

        # 버튼들
        self.btn_search = QPushButton("조회")
        self.btn_search.setStyleSheet("background-color: #1976D2; color: white; font-weight: bold; padding: 5px 15px;")
        self.btn_search.clicked.connect(self.calculate_and_display_fifo)
        search_layout.addWidget(self.btn_search)

        self.btn_this_month = QPushButton("당월 전체")
        self.btn_this_month.setStyleSheet("background-color: #757575; color: white; padding: 5px 10px;")
        self.btn_this_month.clicked.connect(self.set_period_this_month)
        search_layout.addWidget(self.btn_this_month)

        search_layout.addStretch()
        main_layout.addWidget(search_group)

        # =================================================================
        # 2. 중앙 데이터 표시 테이블 영역
        # =================================================================
        table_group = QGroupBox("선입선출 기반 입출고 종합 타임라인")
        table_layout = QVBoxLayout(table_group)

        self.table_status = QTableWidget()
        self.table_status.setColumnCount(11)
        self.table_status.setHorizontalHeaderLabels([
            "일자", "구분", "품명", "규격", 
            "입고수량", "입고단가", "사용수량", 
            "현재고(FIFO)", "적용단가(FIFO)", "재고금액 평가", "비고/출처"
        ])
        self.table_status.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_status.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_status.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table_layout.addWidget(self.table_status)

        main_layout.addWidget(table_group)

    def set_period_this_month(self):
        """조회 기간을 당월 1일부터 오늘까지로 셋팅"""
        current_date = QDate.currentDate()
        self.date_start.setDate(QDate(current_date.year(), current_date.month(), 1))
        self.date_end.setDate(current_date)
        self.calculate_and_display_fifo()

    def load_item_combobox(self):
        """DB에 등록된 품목 리스트를 콤보박스에 로드"""
        self.combo_item_filter.blockSignals(True)
        self.combo_item_filter.clear()
        self.combo_item_filter.addItem("— 전체 품목 조회 —", "ALL")

        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            # 마스터 테이블 혹은 입고 이력이 있는 품목 추출
            cursor.execute("SELECT DISTINCT item_name, spec FROM material_items ORDER BY item_name, spec")
            rows = cursor.fetchall()
            for row in rows:
                display_text = f"{row[0]} ({row[1]})" if row[1] else row[0]
                user_data = {"item_name": row[0], "spec": row[1]}
                self.combo_item_filter.addItem(display_text, user_data)
            conn.close()
        except Exception as e:
            print(f"품목 로드 오류: {e}")
        
        self.combo_item_filter.blockSignals(False)

    def calculate_and_display_fifo(self):
        """핵심: 선입선출 연산 알고리즘 및 테이블 바인딩 (재고 가치 평가 버그 수정 완료)"""
        start_date = self.date_start.date().toString("yyyy-MM-dd")
        end_date = self.date_end.date().toString("yyyy-MM-dd")
        
        selected_index = self.combo_item_filter.currentIndex()
        selected_data = self.combo_item_filter.itemData(selected_index)

        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()

            # 1. 대상 품목 선정 (전체 혹은 선택 품목)
            if selected_data == "ALL" or selected_data is None:
                cursor.execute("SELECT DISTINCT item_name, spec FROM inbound_ledger")
                target_items = cursor.fetchall()
            else:
                target_items = [(selected_data["item_name"], selected_data["spec"])]

            all_timeline_data = []

            for item_name, spec in target_items:
                # 해당 품목의 모든 입고 데이터 가져오기 (시간 순서대로 정렬)
                cursor.execute("""
                    SELECT id, in_date, qty, unit_price, remarks 
                    FROM inbound_ledger 
                    WHERE item_name = %s AND (spec = %s OR (spec IS NULL AND %s IS NULL))
                    ORDER BY in_date ASC, id ASC
                """, (item_name, spec, spec))
                inbounds = [
                    {"id": r[0], "date": r[1], "qty": r[2], "price": r[3], "remained": r[2], "remarks": r[4]} 
                    for r in cursor.fetchall()
                ]

                # 해당 품목의 모든 사용(출고) 데이터 가져오기 (시간 순서대로 정렬)
                cursor.execute("""
                    SELECT id, use_date, qty, usage_type, dong, ho 
                    FROM usage_ledger 
                    WHERE item_name = %s AND (spec = %s OR (spec IS NULL AND %s IS NULL))
                    ORDER BY use_date ASC, id ASC
                """, (item_name, spec, spec))
                usages = [
                    {"id": r[0], "date": r[1], "qty": r[2], "type": r[3], "dong": r[4], "ho": r[5], "fifo_details": []} 
                    for r in cursor.fetchall()
                ]

                # --- 🌟 [핵심 개선] 통합 시뮬레이션을 위한 타임라인 재구성 🌟 ---
                # 입고와 출고를 실제 발생한 '날짜와 ID' 순서대로 정렬하여 실시간으로 재고를 추적합니다.
                combined_events = []
                for ib in inbounds:
                    combined_events.append({"type": "입고", "date": ib["date"], "id": ib["id"], "raw_data": ib})
                for us in usages:
                    combined_events.append({"type": "사용", "date": us["date"], "id": us["id"], "raw_data": us})
                
                # 날짜 순 정렬 (날짜가 같으면 입고를 먼저 처리하거나 ID 순으로 정렬)
                combined_events.sort(key=lambda x: (x["date"], 0 if x["type"] == "입고" else 1, x["id"]))

                # 실시간 추적용 가상 창고 배열 (현재 남아있는 입고 배치들을 담아둠)
                warehouse_stock = []
                running_stock = 0

                for event in combined_events:
                    if event["type"] == "입고":
                        ib = event["raw_data"]
                        # 창고 입고 처리
                        warehouse_stock.append({"price": ib["price"], "remained": ib["qty"]})
                        running_stock += ib["qty"]

                        # 🌟 [버그 수정] 입고 시점의 정확한 자재별 합산 재고 금액 산출
                        current_valuation = sum(stock["remained"] * stock["price"] for stock in warehouse_stock)
                        # 적용 단가는 직관성을 위해 이번에 새로 들어온 입고 단가를 표기
                        current_applied_price = ib["price"]

                        all_timeline_data.append({
                            "date": ib["date"], "type": "입고", "item_name": item_name, "spec": spec,
                            "in_qty": ib["qty"], "in_price": ib["price"], "use_qty": 0,
                            "running_stock": running_stock, "applied_price": current_applied_price,
                            "valuation": current_valuation, "remarks": ib["remarks"]
                        })

                    elif event["type"] == "사용":
                        us = event["raw_data"]
                        use_qty_to_deduct = us["qty"]
                        running_stock -= us["qty"]
                        
                        # 선입선출(FIFO) 차감 엔진 가동
                        for stock in warehouse_stock:
                            if use_qty_to_deduct <= 0:
                                break
                            if stock["remained"] <= 0:
                                continue

                            if stock["remained"] >= use_qty_to_deduct:
                                stock["remained"] -= use_qty_to_deduct
                                use_qty_to_deduct = 0
                                break
                            else:
                                use_qty_to_deduct -= stock["remained"]
                                stock["remained"] = 0

                        # 창고에서 수량이 0이 된 바구니는 필터링해서 정리해도 되지만, 
                        # 가치 평가 계산을 위해 0인 상태로 남겨두어도 무방합니다.
                        
                        # 🌟 [버그 수정] 사용 시점에 창고에 진짜 "남아있는" 자재들의 단가와 수량을 각각 곱해서 합산!
                        current_valuation = sum(stock["remained"] * stock["price"] for stock in warehouse_stock)
                        
                        # 가출고(입고보다 출고가 많음) 발생 시 예외 처리
                        if use_qty_to_deduct > 0:
                            current_valuation -= (use_qty_to_deduct * 0) # 부족분은 0원 처리

                        # 현재 창고에서 가장 오래된(선입) 자재의 단가를 '현재 적용 단가' 필드에 대표로 노출
                        next_applied_price = 0
                        for stock in warehouse_stock:
                            if stock["remained"] > 0:
                                next_applied_price = stock["price"]
                                break

                        loc_info = f"[{us['type']}] {us['dong']}동 {us['ho']}호" if us['dong'] else f"[{us['type']}]"

                        all_timeline_data.append({
                            "date": us["date"], "type": "사용", "item_name": item_name, "spec": spec,
                            "in_qty": 0, "in_price": 0, "use_qty": us["qty"],
                            "running_stock": running_stock, "applied_price": next_applied_price,
                            "valuation": current_valuation, "remarks": loc_info
                        })

            conn.close()

            # 2. 날짜 기준 정렬 및 사용자가 지정한 시작~끝 기간 필터링 처리
            all_timeline_data.sort(key=lambda x: (x["date"], x["item_name"]))
            filtered_data = [
                d for d in all_timeline_data if start_date <= d["date"] <= end_date
            ]

            # 3. 테이블 UI 컴포넌트 출력 및 바인딩
            self.table_status.setRowCount(0)
            for row_idx, data in enumerate(filtered_data):
                self.table_status.insertRow(row_idx)
                
                # 셀 아이템 생성 함수
                def make_item(text, alignment=Qt.AlignCenter, is_number=False):
                    if is_number and isinstance(text, (int, float)):
                        item = QTableWidgetItem(f"{text:,}")
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    else:
                        item = QTableWidgetItem(str(text))
                        item.setTextAlignment(alignment | Qt.AlignVCenter)
                    return item

                self.table_status.setItem(row_idx, 0, make_item(data["date"]))
                
                type_item = make_item(data["type"])
                if data["type"] == "입고":
                    type_item.setForeground(Qt.blue)
                else:
                    type_item.setForeground(Qt.red)
                self.table_status.setItem(row_idx, 1, type_item)
                
                self.table_status.setItem(row_idx, 2, make_item(data["item_name"], Qt.AlignLeft))
                self.table_status.setItem(row_idx, 3, make_item(data["spec"] if data["spec"] else "", Qt.AlignLeft))
                
                # 수량 및 금액
                self.table_status.setItem(row_idx, 4, make_item(data["in_qty"] if data["in_qty"] > 0 else "", is_number=True))
                self.table_status.setItem(row_idx, 5, make_item(data["in_price"] if data["in_price"] > 0 else "", is_number=True))
                self.table_status.setItem(row_idx, 6, make_item(data["use_qty"] if data["use_qty"] > 0 else "", is_number=True))
                
                # 실시간 FIFO 결과물 데이터
                self.table_status.setItem(row_idx, 7, make_item(data["running_stock"], is_number=True))
                self.table_status.setItem(row_idx, 8, make_item(data["applied_price"], is_number=True))
                self.table_status.setItem(row_idx, 9, make_item(data["valuation"], is_number=True))
                self.table_status.setItem(row_idx, 10, make_item(data["remarks"], Qt.AlignLeft))

            self.table_status.resizeColumnsToContents()

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "FIFO 연산 오류", f"선입선출 재고 산출 중 시스템 오류 발생:\n{str(e)}")