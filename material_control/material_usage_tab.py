# material_usage_tab.py
import sys
import os
import shutil
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor, QPixmap
import database
from material_usage_ui import UsageTabUI

class UsageTab(QWidget):
    def __init__(self, user_name="미인증"):
        super().__init__()
        self.current_user = user_name
        
        self.is_edit_mode = False
        self.editing_row_id = None
        self.is_loading_row = False 
        self.is_syncing_ho_disp = False # [추가] 공용 상태 양방향 연동 무한루프 방지 플래그

        # 🌟 사진 저장을 위한 별도 디렉토리 설정 (usage_images)
        self.image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usage_images")
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)

        # 개별 사진 경로 보관 임시 변수
        self.selected_photos = [None, None, None]

        # 1. UI 스킨 결합 및 변수 참조 연결
        self.ui = UsageTabUI()
        self.ui.setup_ui(self)
        self.bind_ui_variables()

        # 2. 시그널 바인딩 및 데이터 로드
        self.connect_signals()
        self.init_combobox_data()
        self.table_display_usage()

    def bind_ui_variables(self):
        """UI 파일의 컴포넌트들을 기존 로직 변수명과 일치시켜 소스 수정 최소화"""
        self.comboType = self.ui.comboType
        self.comboDong = self.ui.comboDong
        self.comboHo = self.ui.comboHo
        self.chkFloorCorridor = self.ui.chkFloorCorridor # 🌟 참조 추가
        self.lblFloorStatus = self.ui.lblFloorStatus     # 🌟 참조 추가
        self.comboDiscipline = self.ui.comboDiscipline
        self.CB_Item = self.ui.CB_Item
        self.CB_Spec = self.ui.CB_Spec
        self.LE_CurrentStock = self.ui.LE_CurrentStock
        self.lineEditUseQty = self.ui.lineEditUseQty
        self.lineEditUseRemarks = self.ui.lineEditUseRemarks
        self.tableWidgetUse = self.ui.tableWidgetUse
        self.group_box_use = self.ui.group_box_use
        self.btn_save_use = self.ui.btn_save_use
        self.btn_cancel_use_edit = self.ui.btn_cancel_use_edit
        self.dateEditUse = self.ui.dateEditUse
        self.photo_widgets = self.ui.photo_widgets
        self.lbl_previews = self.ui.lbl_previews # 하단 액자 참조 추가

    # 🌟 [신규 추가] 층 복도 체크박스 핵심 알고리즘 함수
    def update_floor_corridor_logic(self):
        ho_text = self.comboHo.currentText().strip()
        
        # 체크박스가 켜져있을 때만 층 복도 분석 작동
        if self.chkFloorCorridor.isChecked():
            # 구분 값을 자동으로 '공용'으로 스위칭해 줍니다.
            self.comboType.setCurrentText("공용")
            
            if ho_text.isdigit() and len(ho_text) >= 3:
                # 3자리(예: 302 -> 3층), 4자리(예: 1903 -> 19층) 앞부분 추출
                floor = ho_text[:-2]
                self.lblFloorStatus.setText(f"➔ {floor}층 복도 작업")
            else:
                self.lblFloorStatus.setText("➔ (호수 입력 필요)")
        else:
            self.lblFloorStatus.setText("")

    # 🌟 [신규 추가] 사진 선택 및 해제 핸들러
    def select_photo_file(self, idx):
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"사진 {idx+1} 선택", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.selected_photos[idx] = file_path
            self.photo_widgets[idx]["label"].setText(os.path.basename(file_path))
            self.photo_widgets[idx]["label"].setStyleSheet("color: #2196F3; font-weight: bold;")

    def remove_photo_selection(self, idx):
        self.selected_photos[idx] = None
        self.photo_widgets[idx]["label"].setText(f"사진 {idx+1}: 등록되지 않음")
        self.photo_widgets[idx]["label"].setStyleSheet("color: gray;")

    def connect_signals(self):
        """UI 컴포넌트 기능과 파이썬 메서드 연결"""
        self.comboType.currentTextChanged.connect(self.handle_type_change)
        self.comboDong.currentTextChanged.connect(self.handle_dong_change)
        
        # [수정] 호수와 공종의 변경 감지 시그널을 상호 연동 핸들러 함수로 연결
        self.comboHo.currentTextChanged.connect(self.handle_ho_change)
        self.comboDiscipline.currentTextChanged.connect(self.handle_discipline_change)
        
        self.CB_Item.currentTextChanged.connect(self.handle_item_change)
        self.CB_Spec.currentTextChanged.connect(self.update_stock_display)
        self.tableWidgetUse.itemSelectionChanged.connect(self.highlight_selected_row)
        
        # 버튼 처리 시그널 연결
        self.btn_save_use.clicked.connect(self.process_usage_save)
        self.ui.btn_edit_use_row.clicked.connect(self.load_selected_use_row)
        self.ui.btn_delete_use_row.clicked.connect(self.delete_selected_use_row)
        self.btn_cancel_use_edit.clicked.connect(self.clear_usage_fields)

        # 층 복도 관련 시그널
        self.comboHo.currentTextChanged.connect(self.update_floor_corridor_logic)
        self.chkFloorCorridor.stateChanged.connect(self.update_floor_corridor_logic)

        self.comboDong.currentTextChanged.connect(self.filter_ho_by_dong)
        self.comboItemName.currentTextChanged.connect(self.filter_spec_by_item)
        
        # 🌟 [신규 추가] UI 상의 사진 등록/X 버튼 수동 이벤트 결합 (유실 차단)
        for i in range(3):
            self.photo_widgets[i]["btn_add"].clicked.connect(lambda checked, idx=i: self.select_photo_file(idx))
            self.photo_widgets[i]["btn_del"].clicked.connect(lambda checked, idx=i: self.remove_photo_selection(idx))

        # 🌟 [신규 추가] 테이블 행 클릭 시 하단에 미리보기가 뜨도록 바인딩
        self.tableWidgetUse.cellClicked.connect(self.show_photo_preview_from_table)

    def update_floor_corridor_logic(self):
        ho_text = self.comboHo.currentText().strip()
        if self.chkFloorCorridor.isChecked():
            self.comboType.setCurrentText("공용")
            if ho_text.isdigit() and len(ho_text) >= 3:
                floor = ho_text[:-2]
                self.lblFloorStatus.setText(f"➔ {floor}층 복도 작업")
            else:
                self.lblFloorStatus.setText("➔ (호수 입력 필요)")
        else:
            self.lblFloorStatus.setText("")

    # 파일 탐색기 연동 사진 등록 기능
    def select_photo_file(self, idx):
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"사진 {idx+1} 선택", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.selected_photos[idx] = file_path
            self.photo_widgets[idx]["label"].setText(os.path.basename(file_path))
            self.photo_widgets[idx]["label"].setStyleSheet("color: #2196F3; font-weight: bold;")

    def remove_photo_selection(self, idx):
        self.selected_photos[idx] = None
        self.photo_widgets[idx]["label"].setText(f"사진 {idx+1}: 등록되지 않음")
        self.photo_widgets[idx]["label"].setStyleSheet("color: gray;")

    # 🌟 [신규 추가] 테이블 클릭 시 하단 레이블에 이미지를 비율 맞춰 채우는 함수
    def show_photo_preview_from_table(self, row, column):
        for i in range(3):
            # 사용 테이블에서 9, 10, 11번 셀이 각각 사진1, 사진2, 사진3 정보입니다.
            item = self.tableWidgetUse.item(row, 9 + i)
            file_name = item.text().strip() if item else ""
            
            if file_name and file_name != "None" and "use_" in file_name:
                full_path = os.path.join(self.image_dir, file_name)
                if os.path.exists(full_path):
                    pixmap = QPixmap(full_path)
                    if not pixmap.isNull():
                        scaled_p = pixmap.scaled(
                            self.lbl_previews[i].width(), 
                            self.lbl_previews[i].height(), 
                            Qt.KeepAspectRatio, 
                            Qt.SmoothTransformation
                        )
                        self.lbl_previews[i].setPixmap(scaled_p)
                        self.lbl_previews[i].setStyleSheet("border: 1px solid #2196F3; background-color: #FFFFFF;")
                        continue
                        
            # 매칭 사진이 없으면 액자 초기화
            self.lbl_previews[i].clear()
            self.lbl_previews[i].setText(f"사진 {i+1} 없음")
            self.lbl_previews[i].setStyleSheet("border: 1px dashed #BDBDBD; background-color: #FAFAFA; color: #9E9E9E; font-size: 11px;")

    # =================================================================
    # 비즈니스 데이터 처리 및 연동 로직 코드
    # =================================================================
    def update_stock_display(self):
        item_name = self.CB_Item.currentText().strip()
        spec = self.CB_Spec.currentText().strip()
        if item_name and spec:
            try:
                stock = database.get_current_stock(item_name, spec)
                self.LE_CurrentStock.setText(f"{stock:,} 개")
            except:
                self.LE_CurrentStock.setText("조회 오류")
        else:
            self.LE_CurrentStock.clear()

    def init_combobox_data(self):
        self.handle_type_change(self.comboType.currentText())

    def handle_type_change(self, current_type):
        if self.is_loading_row:
            return
        self.comboDong.blockSignals(True)
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
            self.comboDong.blockSignals(False)
            self.comboDong.setCurrentText("999") 
            self.handle_dong_change("999")
        else:
            index = self.comboDong.findText("101")
            self.comboDong.blockSignals(False)
            if index >= 0:
                self.comboDong.setCurrentIndex(index) 
            else:
                self.comboDong.setCurrentIndex(0)
            self.handle_dong_change(self.comboDong.currentText())

    def handle_dong_change(self, selected_dong):
        if not selected_dong or self.is_loading_row:
            return
        self.sync_ho_combo(selected_dong)
        
        if selected_dong == "999":
            self.comboDiscipline.blockSignals(True)
            self.comboDiscipline.clear()
            for i in range(self.comboHo.count()):
                self.comboDiscipline.addItem(self.comboHo.itemText(i))
            self.comboDiscipline.blockSignals(False)
            
            if self.comboHo.count() > 0:
                first_ho_text = self.comboHo.itemText(0)
                self.comboDiscipline.setCurrentText(first_ho_text)
                self.sync_items_by_discipline(first_ho_text)
        else:
            self.comboDiscipline.blockSignals(True)
            self.comboDiscipline.clear()
            
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT discipline FROM inbound_ledger WHERE discipline IS NOT NULL AND discipline != '' ORDER BY discipline ASC")
            disciplines = cursor.fetchall()
            conn.close()
            
            for disp in disciplines:
                self.comboDiscipline.addItem(str(disp[0]))
                
            self.comboDiscipline.blockSignals(False)
            if self.comboDiscipline.count() > 0:
                self.comboDiscipline.setCurrentIndex(0)
                self.sync_items_by_discipline(self.comboDiscipline.currentText())

    # [핵심 기능 수정] 호수 변경 시 공종 양방향 동기화
    def handle_ho_change(self, selected_ho):
        if not selected_ho or self.is_loading_row or self.is_syncing_ho_disp:
            return
            
        if self.comboType.currentText() == "공용" and self.comboDong.currentText() == "999":
            self.is_syncing_ho_disp = True
            self.comboDiscipline.setCurrentText(selected_ho)
            self.is_syncing_ho_disp = False
            self.sync_items_by_discipline(selected_ho)

    # [핵심 기능 수정] 공종 변경 시 호수 양방향 동기화
    def handle_discipline_change(self, selected_disp):
        if not selected_disp or self.is_loading_row or self.is_syncing_ho_disp:
            return
            
        if self.comboType.currentText() == "공용" and self.comboDong.currentText() == "999":
            self.is_syncing_ho_disp = True
            self.comboHo.setCurrentText(selected_disp)
            self.is_syncing_ho_disp = False
            
        self.sync_items_by_discipline(selected_disp)

    def sync_ho_combo(self, selected_dong):
        if not selected_dong or self.is_loading_row:
            return
        self.comboHo.blockSignals(True)
        self.comboHo.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ho FROM dongho_master WHERE dong = %s ORDER BY CAST(ho AS INTEGER) ASC, ho ASC", (selected_dong,))
        hos = cursor.fetchall()
        conn.close()
        
        for h in hos:
            self.comboHo.addItem(str(h[0]))
            
        if self.comboHo.count() > 0:
            self.comboHo.setCurrentIndex(0) 
        self.comboHo.blockSignals(False)

    def sync_items_by_discipline(self, discipline):
        if self.is_loading_row or not discipline:
            return
        self.CB_Item.blockSignals(True)
        self.CB_Item.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT item_name FROM inbound_ledger WHERE discipline = %s ORDER BY item_name ASC", (discipline,))
        items = cursor.fetchall()
        conn.close()
        
        for i in items:
            self.CB_Item.addItem(str(i[0]))
            
        self.CB_Item.blockSignals(False)
        self.handle_item_change(self.CB_Item.currentText())

    def handle_item_change(self, item_name):
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
            WHERE discipline = %s AND item_name = %s ORDER BY spec ASC
        """, (self.comboDiscipline.currentText(), item_name))
        specs = cursor.fetchall()
        conn.close()
        
        for s in specs:
            self.CB_Spec.addItem(str(s[0]))
        self.CB_Spec.blockSignals(False)

    def highlight_selected_row(self):
        for r in range(self.tableWidgetUse.rowCount()):
            bg_color = QColor(245, 247, 250) if (r % 4) in [2, 3] else QColor(255, 255, 255)
            for c in range(self.tableWidgetUse.columnCount()):
                item = self.tableWidgetUse.item(r, c)
                if item: item.setBackground(bg_color)
                    
        current_row = self.tableWidgetUse.currentRow()
        if current_row >= 0:
            highlight_color = QColor(255, 224, 178) 
            for c in range(self.tableWidgetUse.columnCount()):
                item = self.tableWidgetUse.item(current_row, c)
                if item: item.setBackground(highlight_color)

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
        
        # 🌟 사진 파일 처리 및 보관 복사
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        final_photo_names = [None, None, None]
        if self.is_edit_mode:
            cursor.execute("SELECT photo1, photo2, photo3 FROM usage_ledger WHERE id = %s", (self.editing_row_id,))
            old_photos = cursor.fetchone()
            if old_photos:
                final_photo_names = list(old_photos)

        for i in range(3):
            file_src = self.selected_photos[i]
            if file_src:
                if final_photo_names[i]:
                    old_path = os.path.join(self.image_dir, final_photo_names[i])
                    if os.path.exists(old_path): os.remove(old_path)
                
                ext = os.path.splitext(file_src)[1]
                new_filename = f"use_{int(time.time())}_{i+1}{ext}"
                try:
                    shutil.copy(file_src, os.path.join(self.image_dir, new_filename))
                    final_photo_names[i] = new_filename
                except Exception as e:
                    QMessageBox.critical(self, "사진 복사 실패", f"사진 에러: {e}")
            else:
                if self.is_edit_mode and self.photo_widgets[i]["label"].text() == f"사진 {i+1}: 등록되지 않음":
                    if final_photo_names[i]:
                        old_path = os.path.join(self.image_dir, final_photo_names[i])
                        if os.path.exists(old_path): os.remove(old_path)
                        final_photo_names[i] = None

        if self.is_edit_mode:
            cursor.execute("""
                UPDATE usage_ledger 
                SET use_date=%s, usage_type=%s, dong=%s, ho=%s, discipline=%s, item_name=%s, spec=%s, qty=%s, remarks=%s, worker=%s,
                    photo1=%s, photo2=%s, photo3=%s
                WHERE id=%s
            """, (use_date, usage_type, dong, ho, discipline, item_name, spec, qty, remarks, self.current_user,
                  final_photo_names[0], final_photo_names[1], final_photo_names[2], self.editing_row_id))
            QMessageBox.information(self, "수정 완료", "출고 사용 대장이 수정되었습니다.")
        else:
            cursor.execute("""
                INSERT INTO usage_ledger (use_date, usage_type, dong, ho, discipline, item_name, spec, qty, remarks, worker, photo1, photo2, photo3)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (use_date, usage_type, dong, ho, discipline, item_name, spec, qty, remarks, self.current_user,
                  final_photo_names[0], final_photo_names[1], final_photo_names[2]))
            QMessageBox.information(self, "등록 완료", "자재 사용 내역이 대장에 등록되었습니다.")
            
        conn.commit()
        conn.close()
        
        self.clear_usage_fields()
        self.table_display_usage()

        try:
            current_stock = database.get_current_stock(item_name, spec)
            if self.is_edit_mode:
                conn = database.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT qty FROM usage_ledger WHERE id = %s", (self.editing_row_id,))
                old_qty_res = cursor.fetchone()
                conn.close()
                if old_qty_res: current_stock += old_qty_res[0]

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
                SET use_date=%s, usage_type=%s, dong=%s, ho=%s, discipline=%s, item_name=%s, spec=%s, qty=%s, remarks=%s, worker=%s
                WHERE id = %s
            """, (use_date, usage_type, dong, ho, discipline, item_name, spec, qty, remarks, self.current_user, self.editing_row_id))
            conn.commit()
            QMessageBox.information(self, "수정 성공", "자재 출고/사용 내역 수정이 완료되었습니다.")
        else:
            cursor.execute("""
                INSERT INTO usage_ledger (use_date, usage_type, dong, ho, discipline, item_name, spec, qty, remarks, worker)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            WHERE use_date=%s AND usage_type=%s AND dong=%s AND ho=%s AND item_name=%s AND qty=%s
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
                conn = database.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT ho FROM dongho_master WHERE dong = '999'")
                for h in cursor.fetchall(): self.comboHo.addItem(str(h[0]))
                conn.close()
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

            # 사진 데이터 역로드
            self.selected_photos = [None, None, None]
            for i in range(3):
                p_name = result[9 + i]
                if p_name:
                    self.photo_widgets[i]["label"].setText(str(p_name))
                    self.photo_widgets[i]["label"].setStyleSheet("color: #1976D2; font-weight: bold;")
                else:
                    self.photo_widgets[i]["label"].setText(f"사진 {i+1}: 등록되지 않음")
                    self.photo_widgets[i]["label"].setStyleSheet("color: gray;")
            
            self.is_loading_row = False 
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
        
        self.lineEditUseQty.clear()
        self.lineEditUseRemarks.clear()
        self.LE_CurrentStock.clear()  

        self.selected_photos = [None, None, None]
        for i in range(3):
            self.photo_widgets[i]["label"].setText(f"사진 {i+1}: 등록되지 않음")
            self.photo_widgets[i]["label"].setStyleSheet("color: gray;")
            self.lbl_previews[i].clear()
            self.lbl_previews[i].setText(f"사진 {i+1} 없음")
            self.lbl_previews[i].setStyleSheet("border: 1px dashed #BDBDBD; background-color: #FAFAFA; color: #9E9E9E; font-size: 11px;")
        
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
            
        if QMessageBox.question(self, '최종 확인', '선택한 사용 내역 기록을 영구 삭제하시겠습니까%s', QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            use_date = self.tableWidgetUse.item(current_row, 0).text()
            dong = self.tableWidgetUse.item(current_row, 2).text()
            ho = self.tableWidgetUse.item(current_row, 3).text()
            item_name = self.tableWidgetUse.item(current_row, 5).text()
            qty = int(self.tableWidgetUse.item(current_row, 7).text().replace(",", ""))
            
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM usage_ledger 
                WHERE use_date=%s AND dong=%s AND ho=%s AND item_name=%s AND qty=%s
            """, (use_date, dong, ho, item_name, qty))
            conn.commit()
            conn.close()
            
            if self.is_edit_mode: self.clear_usage_fields()
            self.table_display_usage()
            QMessageBox.information(self, "삭제 성공", "선택 정보가 사용 대장에서 정상 제외되었습니다.")

    def table_display_usage(self):
        self.tableWidgetUse.setRowCount(0)
        self.tableWidgetUse.setSortingEnabled(False)
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        # 🌟 사진 파일 컬럼(photo1, 2, 3)을 포함하도록 쿼리 확장
        cursor.execute("""
            SELECT use_date, usage_type, dong, ho, discipline, item_name, spec, qty, remarks, photo1, photo2, photo3, worker, id 
            FROM usage_ledger ORDER BY id DESC
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