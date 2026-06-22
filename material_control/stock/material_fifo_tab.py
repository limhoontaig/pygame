# material_fifo_status_tab.py
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QDateEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QMessageBox, QComboBox
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor
import common.database as database

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
        self.table_status.setColumnCount(18)
        self.table_status.setHorizontalHeaderLabels([
            "구분일자", "구분", "공종", "품목명", "규격",              # 0~4
            "입고수량", "입고단가", "입고금액",                        # 5~7
            "사용수량", "사용단가", "사용금액", "매칭입고일",          # 8~11
            "현재고(FIFO)", "적용단가(FIFO)", "재고금액 평가",         # 12~14
            "공동/세대 구분", "동", "호", "비고/출처"                 # 15~18 (동, 호 완전 분리)
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
        """핵심: 선입선출 분할 매칭 및 18칼럼 UI 그리드 완벽 바인딩 (동/호 칼럼 완전 분리 버전)"""
        start_date = self.date_start.date().toString("yyyy-MM-dd")
        end_date = self.date_end.date().toString("yyyy-MM-dd")
        
        selected_index = self.combo_item_filter.currentIndex()
        selected_data = self.combo_item_filter.itemData(selected_index)

        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()

            if selected_data == "ALL" or selected_data is None:
                cursor.execute("SELECT DISTINCT item_name, spec FROM inbound_ledger")
                target_items = cursor.fetchall()
            else:
                target_items = [(selected_data["item_name"], selected_data["spec"])]

            all_timeline_data = []

            for item_name, spec in target_items:
                # 1. 입고 데이터 가져오기
                cursor.execute("""
                    SELECT id, in_date, qty, unit_price, remarks, discipline 
                    FROM inbound_ledger 
                    WHERE item_name = %s AND (spec = %s OR (spec IS NULL AND %s IS NULL))
                    ORDER BY in_date ASC, id ASC
                """, (item_name, spec, spec))
                inbounds = [
                    {"id": r[0], "date": r[1], "qty": r[2], "price": r[3], "remarks": r[4], "discipline": r[5]} 
                    for r in cursor.fetchall()
                ]

                # 2. 사용 데이터 가져오기 (동, 호 각각 분리 보존)
                cursor.execute("""
                    SELECT id, use_date, qty, usage_type, dong, ho, discipline 
                    FROM usage_ledger 
                    WHERE item_name = %s AND (spec = %s OR (spec IS NULL AND %s IS NULL))
                    ORDER BY use_date ASC, id ASC
                """, (item_name, spec, spec))
                usages = [
                    {"id": r[0], "date": r[1], "qty": r[2], "type": r[3], "dong": r[4], "ho": r[5], "discipline": r[6]} 
                    for r in cursor.fetchall()
                ]

                # 타임라인 통합 정렬
                combined_events = []
                for ib in inbounds:
                    combined_events.append({"type": "입고", "date": ib["date"], "id": ib["id"], "raw_data": ib})
                for us in usages:
                    combined_events.append({"type": "사용", "date": us["date"], "id": us["id"], "raw_data": us})
                
                combined_events.sort(key=lambda x: (x["date"], 0 if x["type"] == "입고" else 1, x["id"]))

                warehouse_stock = []
                running_stock = 0

                for event in combined_events:
                    if event["type"] == "입고":
                        ib = event["raw_data"]
                        warehouse_stock.append({
                            "in_date": ib["date"], 
                            "price": ib["price"], 
                            "remained": ib["qty"]
                        })
                        running_stock += ib["qty"]
                        current_valuation = sum(s["remained"] * s["price"] for s in warehouse_stock)
                        disp = ib["discipline"] if ib["discipline"] else ""

                        all_timeline_data.append({
                            "date": ib["date"], "type": "입고", "discipline": disp, "item_name": item_name, "spec": spec,
                            "in_qty": ib["qty"], "in_price": ib["price"], "in_total": ib["qty"] * ib["price"],
                            "use_qty": 0, "use_price": 0, "use_total": 0, "matched_in_date": "",
                            "running_stock": running_stock, "applied_price": ib["price"], "valuation": current_valuation,
                            "usage_type": "", "dong": "", "ho": "", "remarks": ib["remarks"]
                        })

                    elif event["type"] == "사용":
                        us = event["raw_data"]
                        use_qty_to_deduct = us["qty"]
                        disp = us["discipline"] if us["discipline"] else ""
                        
                        # FIFO 분할 매칭 처리
                        for stock in warehouse_stock:
                            if use_qty_to_deduct <= 0:
                                break
                            if stock["remained"] <= 0:
                                continue

                            if stock["remained"] >= use_qty_to_deduct:
                                allocated_qty = use_qty_to_deduct
                                stock["remained"] -= use_qty_to_deduct
                                use_qty_to_deduct = 0
                            else:
                                allocated_qty = stock["remained"]
                                use_qty_to_deduct -= stock["remained"]
                                stock["remained"] = 0

                            running_stock -= allocated_qty
                            current_valuation = sum(s["remained"] * s["price"] for s in warehouse_stock)
                            
                            next_applied_price = 0
                            for s in warehouse_stock:
                                if s["remained"] > 0:
                                    next_applied_price = s["price"]
                                    break

                            # 🌟 동/호 데이터 원본 분리 유지 (None 일 때 공백 처리)
                            u_dong = str(us["dong"]).strip() if us["dong"] else ""
                            u_ho = str(us["ho"]).strip() if us["ho"] else ""

                            all_timeline_data.append({
                                "date": us["date"], "type": "사용", "discipline": disp, "item_name": item_name, "spec": spec,
                                "in_qty": 0, "in_price": 0, "in_total": 0,
                                "use_qty": allocated_qty, "use_price": stock["price"], "use_total": allocated_qty * stock["price"], 
                                "matched_in_date": stock["in_date"],
                                "running_stock": running_stock, "applied_price": next_applied_price, "valuation": current_valuation, 
                                "usage_type": us["type"], "dong": u_dong, "ho": u_ho, "remarks": ""
                            })

                        # 가출고(재고 부족) 라인 예외 처리
                        if use_qty_to_deduct > 0:
                            running_stock -= use_qty_to_deduct
                            current_valuation = sum(s["remained"] * s["price"] for s in warehouse_stock)
                            u_dong = str(us["dong"]).strip() if us["dong"] else ""
                            u_ho = str(us["ho"]).strip() if us["ho"] else ""
                            
                            all_timeline_data.append({
                                "date": us["date"], "type": "사용", "discipline": disp, "item_name": item_name, "spec": spec,
                                "in_qty": 0, "in_price": 0, "in_total": 0,
                                "use_qty": use_qty_to_deduct, "use_price": 0, "use_total": 0, "matched_in_date": "입고부족",
                                "running_stock": running_stock, "applied_price": 0, "valuation": current_valuation,
                                "usage_type": us["type"], "dong": u_dong, "ho": u_ho, "remarks": "재고부족분"
                            })

            conn.close()

            # 날짜 정렬 및 기간 필터링
            all_timeline_data.sort(key=lambda x: (x["date"], x["item_name"]))
            filtered_data = [d for d in all_timeline_data if start_date <= d["date"] <= end_date]

            # 3. 18개 칼럼 매핑 및 UI 출력 (인덱스 보정 완벽 적용)
            self.table_status.setRowCount(0)
            for row_idx, data in enumerate(filtered_data):
                self.table_status.insertRow(row_idx)
                
                def make_item(text, alignment=Qt.AlignCenter, is_number=False):
                    if is_number and isinstance(text, (int, float)):
                        item = QTableWidgetItem(f"{text:,}" if text != 0 else "")
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    else:
                        item = QTableWidgetItem(str(text) if text is not None else "")
                        item.setTextAlignment(alignment | Qt.AlignVCenter)
                    return item

                # 0~4: 기본 식별 정보 세트
                self.table_status.setItem(row_idx, 0, make_item(data["date"]))
                type_item = make_item(data["type"])
                type_item.setForeground(Qt.blue if data["type"] == "입고" else Qt.red)
                self.table_status.setItem(row_idx, 1, type_item)
                self.table_status.setItem(row_idx, 2, make_item(data["discipline"]))
                self.table_status.setItem(row_idx, 3, make_item(data["item_name"], Qt.AlignLeft))
                self.table_status.setItem(row_idx, 4, make_item(data["spec"], Qt.AlignLeft))
                
                # 5~7: 입고 세트
                self.table_status.setItem(row_idx, 5, make_item(data["in_qty"] if data["in_qty"] > 0 else "", is_number=True))
                self.table_status.setItem(row_idx, 6, make_item(data["in_price"] if data["in_price"] > 0 else "", is_number=True))
                self.table_status.setItem(row_idx, 7, make_item(data["in_total"] if data["in_total"] > 0 else "", is_number=True))
                
                # 8~11: 사용 세트
                self.table_status.setItem(row_idx, 8, make_item(data["use_qty"] if data["use_qty"] > 0 else "", is_number=True))
                self.table_status.setItem(row_idx, 9, make_item(data["use_price"] if data["use_price"] > 0 else "", is_number=True))
                self.table_status.setItem(row_idx, 10, make_item(data["use_total"] if data["use_total"] > 0 else "", is_number=True))
                
                date_item = make_item(data["matched_in_date"])
                if data["matched_in_date"]:
                    from PyQt5.QtGui import QColor
                    date_item.setForeground(QColor(110, 110, 110))
                self.table_status.setItem(row_idx, 11, date_item)
                
                # 12~14: 실시간 FIFO 재고 분석 세트
                self.table_status.setItem(row_idx, 12, make_item(data["running_stock"], is_number=True))
                self.table_status.setItem(row_idx, 13, make_item(data["applied_price"], is_number=True))
                self.table_status.setItem(row_idx, 14, make_item(data["valuation"], is_number=True))
                
                # 15~17: 공동/세대 구분 및 동, 호 개별 바인딩
                self.table_status.setItem(row_idx, 15, make_item(data["usage_type"])) 
                self.table_status.setItem(row_idx, 16, make_item(data["dong"])) # 👈 [동] 칼럼
                self.table_status.setItem(row_idx, 17, make_item(data["ho"]))   # 👈 [호] 칼럼
                
                # 18: 비고/출처
                self.table_status.setItem(row_idx, 18, make_item(data["remarks"], Qt.AlignLeft))

            self.table_status.resizeColumnsToContents()

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "FIFO 연산 오류", f"화면 바인딩 중 오류 발생:\n{str(e)}")