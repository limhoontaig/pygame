# material_inbound_tab.py

import sys
import os
import shutil
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor, QFont
import database
import pandas as pd

class InboundTab(QWidget):
    def __init__(self, user_name="미인증"):
        super().__init__()
        self.current_user = user_name
        
        # 수정 모드 및 자동 계산 무한 루프 방지 플래그
        self.is_edit_mode = False
        self.editing_row_id = None  
        self.is_calculating = False  # 양방향 계산 오작동 방지용 플래그

        # 🌟 사진 저장을 위한 별도 디렉토리 설정
        self.image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inbound_images")
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)

        # 개별 사진 경로를 임시 저장할 변수 리스트 (경로 문자열 또는 None)
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
        
        # 콤보박스 하단 안내 문구
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
        
        # 단가와 총금액 사이 양방향 계산 기능 안내 문구
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

        # 🌟 (10) [신규 추가] 현장 사진 등록 등록 UI 영역 (3장)
        grid_in.addWidget(QLabel("현장 사진:"), 11, 0)
        photo_main_layout = QVBoxLayout()
        
        self.photo_widgets = [] # 사진 등록 제어를 위한 UI 구성요소 저장 리스트
        for i in range(3):
            p_layout = QHBoxLayout()
            lbl_status = QLabel(f"사진 {i+1}: 등록되지 않음")
            lbl_status.setStyleSheet("color: gray;")
            
            btn_add = QPushButton("등록")
            btn_add.setFixedWidth(50)
            btn_add.clicked.connect(lambda checked, idx=i: self.select_photo_file(idx))
            
            btn_del = QPushButton("X")
            btn_del.setFixedWidth(25)
            btn_del.setStyleSheet("background-color: #757575; color: white; font-weight: bold;")
            btn_del.clicked.connect(lambda checked, idx=i: self.remove_photo_selection(idx))
            
            p_layout.addWidget(lbl_status, 1)
            p_layout.addWidget(btn_add)
            p_layout.addWidget(btn_del)
            photo_main_layout.addLayout(p_layout)
            
            # 참조를 위해 딕셔너리로 보관
            self.photo_widgets.append({"label": lbl_status, "btn_add": btn_add, "btn_del": btn_del})
            
        grid_in.addLayout(photo_main_layout, 11, 1)
        
        # (11) 버튼 영역
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
        
        grid_in.addLayout(button_layout, 12, 0, 1, 2)
        
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

        # 엑셀 다운로드 버튼
        self.btn_export_excel = QPushButton("엑셀 내보내기 (Report)")
        self.btn_export_excel.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold; padding: 6px 12px;")
        self.btn_export_excel.clicked.connect(self.export_to_excel)
        top_bar.addWidget(self.btn_export_excel)
        
        top_bar.addStretch()
        right_layout.addLayout(top_bar)
        
        self.tableWidgetInIn = QTableWidget()
        self.tableWidgetInIn.setColumnCount(13) # 🌟 사진 3개 컬럼 반영하여 10 -> 13 확장
        self.tableWidgetInIn.setHorizontalHeaderLabels([
            "입고일자", "공종", "품명", "규격", "수량", "단가", "총금액", "공급처", "비고", "사진1", "사진2", "사진3", "입력자"
        ])
        self.tableWidgetInIn.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidgetInIn.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.tableWidgetInIn)

        # =================================================================
        # 🌟 [신규 추가] 테이블 선택 행 사진 미리보기 영역 (테이블 하단 배치)
        # =================================================================
        self.preview_group = QGroupBox("선택 자재 사진 미리보기")
        preview_layout = QHBoxLayout(self.preview_group)
        self.preview_group.setFixedHeight(190)  # 하단 영역 높이 고정
        
        self.lbl_previews = []
        for i in range(3):
            lbl_img = QLabel(f"사진 {i+1} 없음")
            lbl_img.setAlignment(Qt.AlignCenter)
            # 깔끔하게 테두리와 배경색을 주어 사진틀 느낌을 내줍니다.
            lbl_img.setStyleSheet("""
                border: 1px dashed #BDBDBD; 
                background-color: #FAFAFA; 
                color: #9E9E9E;
                font-size: 11px;
            """)
            lbl_img.setFixedSize(220, 150)  # 이미지 액자 크기 설정
            preview_layout.addWidget(lbl_img)
            self.lbl_previews.append(lbl_img)
            
        preview_layout.addStretch() # 사진들이 왼쪽에 조밀하게 붙도록 우측 여백 배치
        right_layout.addWidget(self.preview_group) # 우측 메인 레이아웃에 추가
        
        # 메인 레이아웃 구성 마무리 (기존 코드)
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)

        # 🌟 테이블 클릭 시 사진을 띄워줄 이벤트 시그널 바인딩 추가
        self.tableWidgetInIn.cellClicked.connect(self.show_photo_preview_from_table)
        
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)

        # 금액 자동 역산 바인딩
        self.lineEditInQty.textChanged.connect(self.calculate_from_price)
        self.lineEditInPrice.textChanged.connect(self.calculate_from_price)
        self.lineEditInTotalPrice.textChanged.connect(self.calculate_from_total_price)

        # Placeholder 세팅
        self.comboBoxInDiscipline.setPlaceholderText("공종 입력 또는 선택")
        self.comboBoxInName.setPlaceholderText("품명 입력 또는 선택")
        self.comboBoxInSpec.setPlaceholderText("신규 추가 품목")

        # 계층형 필터링 시그널
        self.comboBoxInDiscipline.currentTextChanged.connect(self.filter_name_combo)
        self.comboBoxInName.currentTextChanged.connect(self.filter_spec_combo)

    # =================================================================
    # 🌟 사진 첨부 인터페이스 핸들러
    # =================================================================
    def select_photo_file(self, idx):
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"사진 {idx+1} 선택", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.selected_photos[idx] = file_path
            filename = os.path.basename(file_path)
            self.photo_widgets[idx]["label"].setText(filename)
            self.photo_widgets[idx]["label"].setStyleSheet("color: #2E7D32; font-weight: bold;")

    def remove_photo_selection(self, idx):
        self.selected_photos[idx] = None
        self.photo_widgets[idx]["label"].setText(f"사진 {idx+1}: 등록되지 않음")
        self.photo_widgets[idx]["label"].setStyleSheet("color: gray;")

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
                f"위 정보가 정확합니까? 확인 후 등록됩니다.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                conn.close()
                return
            
            try:
                cursor.execute("INSERT INTO material_items (item_name, spec) VALUES (%s, %s)", (item_name, spec))
                conn.commit()
            except Exception:
                pass

        # 🌟 [사진 파일 처리 저장/수정 핵심 로직]
        final_photo_names = [None, None, None]
        
        # 만약 수정모드라면 기존 DB에 등록되어 있던 이미지 파일명을 먼저 확보함
        if self.is_edit_mode:
            cursor.execute("SELECT photo1, photo2, photo3 FROM inbound_ledger WHERE id = %s", (self.editing_row_id,))
            old_photos = cursor.fetchone()
            if old_photos:
                final_photo_names = list(old_photos)

        for i in range(3):
            file_src = self.selected_photos[i]
            if file_src: # 새 파일이 탐색기에서 선택된 상태인 경우
                # 기존에 파일이 존재했다면 충돌 방지 및 용량 최적화를 위해 먼저 삭제
                if final_photo_names[i]:
                    old_path = os.path.join(self.image_dir, final_photo_names[i])
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                # 타임스탬프 결합형 고유 파일명 생성
                ext = os.path.splitext(file_src)[1]
                new_filename = f"img_{int(time.time())}_{i+1}{ext}"
                file_dest = os.path.join(self.image_dir, new_filename)
                
                try:
                    shutil.copy(file_src, file_dest)
                    final_photo_names[i] = new_filename # 새 파일명으로 갱신
                except Exception as e:
                    QMessageBox.critical(self, "사진 복사 에러", f"사진 {i+1}을 저장소에 복사하지 못했습니다.\n{e}")
            else:
                # 사용자가 X 버튼을 눌러 명시적으로 비운 상태라면 기존 파일 파기
                if self.is_edit_mode and self.photo_widgets[i]["label"].text() == f"사진 {i+1}: 등록되지 않음":
                    if final_photo_names[i]:
                        old_path = os.path.join(self.image_dir, final_photo_names[i])
                        if os.path.exists(old_path):
                            os.remove(old_path)
                        final_photo_names[i] = None

        qty = int(qty_str)
        total_price = int(total_price_str) if total_price_str.isdigit() else 0
        unit_price = int(price_str) if price_str.isdigit() else 0
        
        supplier = self.lineEditInSupplier.text().strip()
        remarks = self.lineEditInRemarks.text().strip()
        in_date = self.dateEditIn.date().toString("yyyy-MM-dd")
        
        if self.is_edit_mode:
            cursor.execute("""
                UPDATE inbound_ledger
                SET in_date=%s, discipline=%s, item_name=%s, spec=%s, qty=%s, unit_price=%s, total_price=%s, 
                    supplier=%s, remarks=%s, photo1=%s, photo2=%s, photo3=%s, worker=%s
                WHERE id = %s
            """, (in_date, discipline, item_name, spec, qty, unit_price, total_price, 
                  supplier, remarks, final_photo_names[0], final_photo_names[1], final_photo_names[2], self.current_user, self.editing_row_id))
            conn.commit()
            QMessageBox.information(self, "수정 완료", "자재 입고 내역이 정상적으로 수정되었습니다.")
        else:
            cursor.execute("""
                INSERT INTO inbound_ledger (in_date, discipline, item_name, spec, qty, unit_price, total_price, supplier, remarks, photo1, photo2, photo3, worker)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (in_date, discipline, item_name, spec, qty, unit_price, total_price, supplier, remarks, 
                  final_photo_names[0], final_photo_names[1], final_photo_names[2], self.current_user))
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
            
        # 🌟 중요: table_display_in에서 숨겨둔 고유 식별 ID 추출
        row_id = self.tableWidgetInIn.item(current_row, 0).data(Qt.UserRole + 1)
        if not row_id:
            QMessageBox.critical(self, "에러", "해당 행의 고유 ID를 조회하지 못했습니다.")
            return

        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT in_date, discipline, item_name, spec, qty, unit_price, total_price, supplier, remarks, photo1, photo2, photo3 
            FROM inbound_ledger WHERE id = %s
        """, (row_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            self.is_edit_mode = True
            self.editing_row_id = row_id
            
            self.dateEditIn.setDate(QDate.fromString(str(result[0]), "yyyy-MM-dd"))
            self.comboBoxInDiscipline.setEditText(str(result[1]) if result[1] else "")
            self.comboBoxInName.setEditText(str(result[2]))
            self.comboBoxInSpec.setEditText(str(result[3]) if result[3] else "")
            
            self.is_calculating = True
            self.lineEditInQty.setText(str(result[4]))
            self.lineEditInPrice.setText(str(result[5]))
            self.lineEditInTotalPrice.setText(str(result[6]))
            self.is_calculating = False
            
            self.lineEditInSupplier.setText(str(result[7]) if result[7] else "")
            self.lineEditInRemarks.setText(str(result[8]) if result[8] else "")
            
            # 🌟 사진 상태 로드 및 동기화
            self.selected_photos = [None, None, None]
            for i in range(3):
                p_name = result[9 + i]
                if p_name:
                    self.photo_widgets[i]["label"].setText(str(p_name))
                    self.photo_widgets[i]["label"].setStyleSheet("color: #1976D2; font-weight: bold;")
                else:
                    self.photo_widgets[i]["label"].setText(f"사진 {i+1}: 등록되지 않음")
                    self.photo_widgets[i]["label"].setStyleSheet("color: gray;")
            
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

        # 사진 데이터 초기화
        self.selected_photos = [None, None, None]
        for i in range(3):
            self.photo_widgets[i]["label"].setText(f"사진 {i+1}: 등록되지 않음")
            self.photo_widgets[i]["label"].setStyleSheet("color: gray;")
        
        # 🌟 [신규 추가] 하단 미리보기 액자도 초기화
        for i in range(3):
            self.lbl_previews[i].clear()
            self.lbl_previews[i].setText(f"사진 {i+1} 없음")
            self.lbl_previews[i].setStyleSheet("""
                border: 1px dashed #BDBDBD; 
                background-color: #FAFAFA; 
                color: #9E9E9E;
                font-size: 11px;
            """)
        
        self.group_box_in.setTitle("자재 입고(등록) 입력")
        self.btn_save_in.setText("입고 내역 등록")
        self.btn_save_in.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 35px;")
        self.btn_cancel_edit.setVisible(False)

    # =================================================================
    # 🌟 [신규 추가] 테이블 행 클릭 시 하단에 실제 사진 표시 로직
    # =================================================================
    from PyQt5.QtGui import QPixmap  # 파일 최상단에 없다면 함수 내부나 상단에 임포트 필수
    
    def show_photo_preview_from_table(self, row, column):
        # 현재 선택된 행의 9, 10, 11번 컬럼이 각각 사진1, 사진2, 사진3 파일명 텍스트입니다.
        for i in range(3):
            col_idx = 9 + i
            item = self.tableWidgetInIn.item(row, col_idx)
            file_name = item.text().strip() if item else ""
            
            # 파일명이 DB에 기록되어 있고, 실제 폴더에 존재할 때
            if file_name and file_name != "None" and "img_" in file_name:
                full_path = os.path.join(self.image_dir, file_name)
                
                if os.path.exists(full_path):
                    pixmap = self.QPixmap(full_path)
                    if not pixmap.isNull():
                        # 액자 크기(220x150)에 맞춰 이미지 비율을 유지(KeepAspectRatio)하며 부드럽게(SmoothTransformation) 축소/확대
                        scaled_pixmap = pixmap.scaled(
                            self.lbl_previews[i].width(), 
                            self.lbl_previews[i].height(), 
                            Qt.KeepAspectRatio, 
                            Qt.SmoothTransformation
                        )
                        self.lbl_previews[i].setPixmap(scaled_pixmap)
                        self.lbl_previews[i].setStyleSheet("border: 1px solid #4CAF50; background-color: #FFFFFF;") # 성공 시 초록 테두리
                        continue
                        
            # 사진 파일이 없거나 유효하지 않은 경우 원상복구
            self.lbl_previews[i].clear()
            self.lbl_previews[i].setText(f"사진 {i+1} 없음")
            self.lbl_previews[i].setStyleSheet("""
                border: 1px dashed #BDBDBD; 
                background-color: #FAFAFA; 
                color: #9E9E9E;
                font-size: 11px;
            """)

    def refresh_all_combos(self):
        self.comboBoxInDiscipline.blockSignals(True)
        self.comboBoxInDiscipline.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT discipline FROM inbound_ledger 
            WHERE discipline IS NOT NULL AND discipline != '' 
            ORDER BY discipline ASC
        """)
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
        
        self.comboBoxInDiscipline.blockSignals(False)
        
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
        self.comboBoxInName.blockSignals(True)
        self.comboBoxInName.clear() 
        
        if not discipline.strip():
            self.comboBoxInName.blockSignals(False)
            self.filter_spec_combo("")
            return

        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT item_name FROM inbound_ledger 
            WHERE discipline = %s AND item_name IS NOT NULL AND item_name != ''
            ORDER BY item_name ASC
        """, (discipline.strip(),))
        items = cursor.fetchall()
        
        if not items:
            cursor.execute("SELECT DISTINCT item_name FROM material_items ORDER BY item_name ASC")
            items = cursor.fetchall()
            
        conn.close()
        
        for i in items:
            self.comboBoxInName.addItem(str(i[0]))
            
        self.comboBoxInName.blockSignals(False)
        
        if self.comboBoxInName.count() > 0:
            self.comboBoxInName.setCurrentIndex(0)
        else:
            self.comboBoxInName.clearEditText()
            
        self.filter_spec_combo(self.comboBoxInName.currentText())

    def filter_spec_combo(self, item_name):
        self.comboBoxInSpec.blockSignals(True)
        self.comboBoxInSpec.clear() 
        
        discipline = self.comboBoxInDiscipline.currentText().strip()
        item_name = item_name.strip()
        
        if not item_name:
            self.comboBoxInSpec.blockSignals(False)
            self.comboBoxInSpec.clearEditText()
            return

        conn = database.get_db_connection()
        cursor = conn.cursor()
        
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
        
        if self.comboBoxInSpec.count() > 0:
            self.comboBoxInSpec.setCurrentIndex(0)
        else:
            self.comboBoxInSpec.clearEditText()

    def table_display_in(self):
        self.tableWidgetInIn.setRowCount(0)
        self.tableWidgetInIn.setSortingEnabled(False)
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        # 🌟 고유 ID 및 사진 컬럼을 포함하여 SELECT 쿼리문 수정
        cursor.execute("""
            SELECT in_date, discipline, item_name, spec, qty, unit_price, total_price, 
                   supplier, remarks, photo1, photo2, photo3, worker, id 
            FROM inbound_ledger 
            ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        for row_idx, row_data in enumerate(rows):
            self.tableWidgetInIn.insertRow(row_idx)
            bg_color = QColor(245, 247, 250) if (row_idx % 4) in [2, 3] else QColor(255, 255, 255)
            
            # row_data[:-1]을 돌며 UI에 바인딩 (id 컬럼 제외)
            for col_idx, value in enumerate(row_data[:-1]):
                if col_idx in [4, 5, 6]: 
                    formatted_val = f"{value:,}" if isinstance(value, (int, float)) else str(value)
                    item = QTableWidgetItem(formatted_val)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setTextAlignment(Qt.AlignCenter)
                
                item.setBackground(bg_color)
                self.tableWidgetInIn.setItem(row_idx, col_idx, item)
            
            # 🌟 [중요 보완] 행의 첫 번째 텍스트 아이템 데이터 영역에 고유 Primary Key ID(row_data[-1]) 정보를 바인딩 및 숨김 처리
            self.tableWidgetInIn.item(row_idx, 0).setData(Qt.UserRole + 1, row_data[-1])
                
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
            
        if QMessageBox.question(self, '확인', '선택한 내역을 삭제하시겠습니까?', QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            # 🌟 숨겨진 고유 ID 안전하게 취득
            row_id = self.tableWidgetInIn.item(current_row, 0).data(Qt.UserRole + 1)
            
            if not row_id:
                QMessageBox.critical(self, "삭제 실패", "선택된 행의 고유 ID 정보를 식별할 수 없습니다.")
                return

            # 물리 삭제용 타겟 리스트 생성 (테이블 9, 10, 11번 컬럼이 사진1, 2, 3)
            photos_to_delete = []
            for i in range(3):
                p_item = self.tableWidgetInIn.item(current_row, 9 + i)
                if p_item and p_item.text().strip() and "img_" in p_item.text():
                    photos_to_delete.append(p_item.text().strip())
            
            try:
                conn = database.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM inbound_ledger WHERE id=%s", (row_id,))
                conn.commit()
                conn.close()
                
                # 이미지 저장소의 물리적 파일 삭제 처리
                for p_name in photos_to_delete:
                    target_file = os.path.join(self.image_dir, p_name)
                    if os.path.exists(target_file):
                        os.remove(target_file)
                
                QMessageBox.information(self, "삭제 완료", "데이터와 연결된 현장 사진이 안전하게 파기되었습니다.")
                self.clear_input_fields()
                self.table_display_in()
                
            except Exception as e:
                QMessageBox.critical(self, "삭제 실패", f"데이터베이스 삭제 중 에러 발생:\n{e}")

    def export_to_excel(self):
        row_count = self.tableWidgetInIn.rowCount()
        column_count = self.tableWidgetInIn.columnCount()
        
        if row_count == 0:
            QMessageBox.warning(self, "추출 실패", "엑셀로 내보낼 데이터가 없습니다.")
            return
            
        default_filename = f"자재입고현황_레포트.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "엑셀 파일 저장", default_filename, "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return 

        try:
            headers = []
            for col in range(column_count):
                headers.append(self.tableWidgetInIn.horizontalHeaderItem(col).text())
                
            table_data = []
            for row in range(row_count):
                row_data = []
                for col in range(column_count):
                    item = self.tableWidgetInIn.item(row, col)
                    val = item.text() if item else ""
                    if col in [4, 5, 6]:
                        val = val.replace(",", "")
                        val = int(val) if val.isdigit() else 0
                    row_data.append(val)
                table_data.append(row_data)
                
            df = pd.DataFrame(table_data, columns=headers)
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name="입고내역_Report")
                
                workbook = writer.book
                worksheet = writer.sheets["입고내역_Report"]
                for col in worksheet.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    col_letter = col[0].column_letter
                    worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

            QMessageBox.information(self, "추출 완료", f"성공적으로 엑셀 레포트가 생성되었습니다.\n경로: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "시스템 에러", f"엑셀 변환 중 오류가 발생했습니다:\n{e}")