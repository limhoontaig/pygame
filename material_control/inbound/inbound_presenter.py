# inbound_presenter.py
import os
import shutil
import time
import pandas as pd
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor, QPixmap
import common.database as database

class InboundPresenter:
    def __init__(self, view):
        self.view = view  # 메인 탭(뷰)에 대한 참조

    def select_photo_file(self, idx):
        file_path, _ = QFileDialog.getOpenFileName(
            self.view, f"사진 {idx+1} 선택", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.view.selected_photos[idx] = file_path
            self.view.photo_widgets[idx]["label"].setText(os.path.basename(file_path))
            self.view.photo_widgets[idx]["label"].setStyleSheet("color: #2E7D32; font-weight: bold;")

    def remove_photo_selection(self, idx):
        self.view.selected_photos[idx] = None
        self.view.photo_widgets[idx]["label"].setText(f"사진 {idx+1}: 등록되지 않음")
        self.view.photo_widgets[idx]["label"].setStyleSheet("color: gray;")

    def calculate_from_price(self):
        if self.view.is_calculating or not (self.view.lineEditInQty.hasFocus() or self.view.lineEditInPrice.hasFocus()):
            return
        qty_str, price_str = self.view.lineEditInQty.text().strip(), self.view.lineEditInPrice.text().strip()
        if qty_str.isdigit() and price_str.isdigit():
            self.view.is_calculating = True
            self.view.lineEditInTotalPrice.setText(str(int(qty_str) * int(price_str)))
            self.view.is_calculating = False
        elif not qty_str or not price_str:
            self.view.is_calculating = True; self.view.lineEditInTotalPrice.clear(); self.view.is_calculating = False

    def calculate_from_total_price(self):
        if self.view.is_calculating or not self.view.lineEditInTotalPrice.hasFocus():
            return
        qty_str, total_str = self.view.lineEditInQty.text().strip(), self.view.lineEditInTotalPrice.text().strip()
        if qty_str.isdigit() and total_str.isdigit():
            qty, total = int(qty_str), int(total_str)
            if qty > 0:
                self.view.is_calculating = True
                self.view.lineEditInPrice.setText(str(total // qty))
                self.view.is_calculating = False
            else:
                self.view.is_calculating = True; self.view.lineEditInPrice.clear(); self.view.is_calculating = False
        elif not total_str:
            self.view.is_calculating = True; self.view.lineEditInPrice.clear(); self.view.is_calculating = False

    # 🌟 [신규 추가] 기간조회 액션 함수
    def search_by_date_range(self):
        start_date = self.view.dateEditStart.date().toString("yyyy-MM-dd")
        end_date = self.view.dateEditEnd.date().toString("yyyy-MM-dd")
        
        if start_date > end_date:
            QMessageBox.warning(self.view, "조회 오류", "시작날짜가 끝날짜보다 늦을 수 없습니다.")
            return
            
        # 테이블 리스트를 기간 조건 조건절로 다시 조회 및 갱신
        self.table_display_in(mode="range", p1=start_date, p2=end_date)

    # 🌟 [신규 추가] 월간보고 액션 함수 (시작 날짜의 '연도-월' 기준)
    def search_by_month(self):
        target_date = self.view.dateEditStart.date()
        year = target_date.year()
        month = target_date.month()
        
        # 시작 날짜의 월의 1일과 말일 계산하여 범위 지정
        start_date = f"{year}-{month:02d}-01"
        # 종료 처리를 간편하게 SQL의 LIKE 'YYYY-MM%' 구문으로 처리하도록 Presenter 레벨 조율
        self.table_display_in(mode="month", p1=f"{year}-{month:02d}%")
        
        # 직관성을 위해 UI 종료 날짜 칸도 해당 월의 마지막 날로 동기화 업데이트 해줌
        last_day = target_date.addMonths(1).addDays(-target_date.day())
        self.view.dateEditEnd.setDate(last_day)

    def process_inbound_save(self):
        view = self.view
        discipline = view.comboBoxInDiscipline.currentText().strip()
        item_name = view.comboBoxInName.currentText().strip()
        spec = view.comboBoxInSpec.currentText().strip()
        qty_str = view.lineEditInQty.text().strip()
        price_str = view.lineEditInPrice.text().strip()
        total_price_str = view.lineEditInTotalPrice.text().strip()
        
        if not item_name:
            QMessageBox.warning(view, "입력 오류", "품명을 선택하거나 입력해 주세요."); return
        if not qty_str or not qty_str.isdigit():
            QMessageBox.warning(view, "입력 오류", "정확한 입고 수량을 숫자로 입력해 주세요."); return

        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM material_items WHERE item_name = %s", (item_name,))
        if not cursor.fetchone()[0] > 0 and not spec:
            QMessageBox.information(view, "신규 품명 안내", f"[{item_name}]은 처음 등록되는 신규 품명입니다.\n규격을 입력해 주세요.")
            view.comboBoxInSpec.setFocus(); conn.close(); return

        cursor.execute("SELECT COUNT(*) FROM material_items WHERE item_name = %s AND spec = %s", (item_name, spec))
        if not cursor.fetchone()[0] > 0:
            if QMessageBox.question(view, "신규 자재 등록 확인", f"시스템에 없는 새 자재 정보입니다.\n등록하시겠습니까?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
                conn.close(); return
            try: cursor.execute("INSERT INTO material_items (item_name, spec) VALUES (%s, %s)", (item_name, spec)); conn.commit()
            except: pass

        final_photo_names = [None, None, None]
        if view.is_edit_mode:
            cursor.execute("SELECT photo1, photo2, photo3 FROM inbound_ledger WHERE id = %s", (view.editing_row_id,))
            old_photos = cursor.fetchone()
            if old_photos: final_photo_names = list(old_photos)

        for i in range(3):
            file_src = view.selected_photos[i]
            if file_src:
                if final_photo_names[i]:
                    old_path = os.path.join(view.image_dir, final_photo_names[i])
                    if os.path.exists(old_path): os.remove(old_path)
                ext = os.path.splitext(file_src)[1]
                new_filename = f"img_{int(time.time())}_{i+1}{ext}"
                try:
                    shutil.copy(file_src, os.path.join(view.image_dir, new_filename))
                    final_photo_names[i] = new_filename
                except Exception as e:
                    QMessageBox.critical(view, "사진 복사 에러", f"사진 복사 실패: {e}")
            else:
                if view.is_edit_mode and view.photo_widgets[i]["label"].text() == f"사진 {i+1}: 등록되지 않음":
                    if final_photo_names[i]:
                        old_path = os.path.join(view.image_dir, final_photo_names[i])
                        if os.path.exists(old_path): os.remove(old_path)
                        final_photo_names[i] = None

        qty, total_price = int(qty_str), (int(total_price_str) if total_price_str.isdigit() else 0)
        unit_price = int(price_str) if price_str.isdigit() else 0
        supplier, remarks = view.lineEditInSupplier.text().strip(), view.lineEditInRemarks.text().strip()
        in_date = view.dateEditIn.date().toString("yyyy-MM-dd")
        
        if view.is_edit_mode:
            cursor.execute("""
                UPDATE inbound_ledger SET in_date=%s, discipline=%s, item_name=%s, spec=%s, qty=%s, unit_price=%s, 
                total_price=%s, supplier=%s, remarks=%s, photo1=%s, photo2=%s, photo3=%s, worker=%s WHERE id = %s
            """, (in_date, discipline, item_name, spec, qty, unit_price, total_price, 
                  supplier, remarks, final_photo_names[0], final_photo_names[1], final_photo_names[2], view.current_user, view.editing_row_id))
            conn.commit(); QMessageBox.information(view, "수정 완료", "자재 내역이 정상적으로 수정되었습니다.")
        else:
            cursor.execute("""
                INSERT INTO inbound_ledger (in_date, discipline, item_name, spec, qty, unit_price, total_price, supplier, remarks, photo1, photo2, photo3, worker)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (in_date, discipline, item_name, spec, qty, unit_price, total_price, supplier, remarks, final_photo_names[0], final_photo_names[1], final_photo_names[2], view.current_user))
            conn.commit(); QMessageBox.information(view, "등록 완료", "입고 내역이 등록되었습니다.")
            
        conn.close()
        view.clear_input_fields(); view.refresh_all_combos(); view.table_display_in()

    def load_selected_row_to_form(self):
        view = self.view
        current_row = view.tableWidgetInIn.currentRow()
        if current_row < 0:
            QMessageBox.warning(view, "선택 오류", "수정할 항목을 선택해 주세요."); return
        row_id = view.tableWidgetInIn.item(current_row, 0).data(Qt.UserRole + 1)

        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT in_date, discipline, item_name, spec, qty, unit_price, total_price, supplier, remarks, photo1, photo2, photo3 FROM inbound_ledger WHERE id = %s", (row_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            view.is_edit_mode = True
            view.editing_row_id = row_id
            view.dateEditIn.setDate(QDate.fromString(str(result[0]), "yyyy-MM-dd"))
            view.comboBoxInDiscipline.setEditText(str(result[1]) if result[1] else "")
            view.comboBoxInName.setEditText(str(result[2]))
            view.comboBoxInSpec.setEditText(str(result[3]) if result[3] else "")
            
            view.is_calculating = True
            view.lineEditInQty.setText(str(result[4]))
            view.lineEditInPrice.setText(str(result[5]))
            view.lineEditInTotalPrice.setText(str(result[6]))
            view.is_calculating = False
            
            view.lineEditInSupplier.setText(str(result[7]) if result[7] else "")
            view.lineEditInRemarks.setText(str(result[8]) if result[8] else "")
            
            view.selected_photos = [None, None, None]
            for i in range(3):
                p_name = result[9 + i]
                if p_name:
                    view.photo_widgets[i]["label"].setText(str(p_name))
                    view.photo_widgets[i]["label"].setStyleSheet("color: #1976D2; font-weight: bold;")
                else:
                    view.photo_widgets[i]["label"].setText(f"사진 {i+1}: 등록되지 않음")
                    view.photo_widgets[i]["label"].setStyleSheet("color: gray;")
            
            view.group_box_in.setTitle("⚠️ 자재 입고 내역 수정 중")
            view.btn_save_in.setText("수정 완료 저장")
            view.btn_save_in.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; height: 35px;")
            view.btn_cancel_edit.setVisible(True)

    def refresh_all_combos(self):
        view = self.view
        view.comboBoxInDiscipline.blockSignals(True); view.comboBoxInDiscipline.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT discipline FROM inbound_ledger WHERE discipline IS NOT NULL AND discipline != '' ORDER BY discipline ASC")
        for d in cursor.fetchall(): view.comboBoxInDiscipline.addItem(str(d[0]))
            
        cursor.execute("SELECT discipline, item_name, spec FROM inbound_ledger ORDER BY id DESC LIMIT 1")
        last_entry = cursor.fetchone()
        conn.close()
        view.comboBoxInDiscipline.blockSignals(False)
        
        if last_entry and not view.is_edit_mode:
            view.comboBoxInDiscipline.setEditText(str(last_entry[0]))
            view.filter_name_combo(str(last_entry[0]))
            view.comboBoxInName.setEditText(str(last_entry[1]))
            view.filter_spec_combo(str(last_entry[1]))
            view.comboBoxInSpec.setEditText(str(last_entry[2]))
        elif not view.is_edit_mode:
            if view.comboBoxInDiscipline.count() > 0:
                view.comboBoxInDiscipline.setCurrentIndex(0)
                view.filter_name_combo(view.comboBoxInDiscipline.currentText())
            else:
                view.comboBoxInDiscipline.clearEditText(); view.comboBoxInName.clear(); view.comboBoxInSpec.clear()

    def filter_name_combo(self, discipline):
        view = self.view
        view.comboBoxInName.blockSignals(True); view.comboBoxInName.clear() 
        if not discipline.strip():
            view.comboBoxInName.blockSignals(False); view.filter_spec_combo(""); return

        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT item_name FROM inbound_ledger WHERE discipline = %s AND item_name IS NOT NULL AND item_name != '' ORDER BY item_name ASC", (discipline.strip(),))
        items = cursor.fetchall()
        if not items:
            cursor.execute("SELECT DISTINCT item_name FROM material_items ORDER BY item_name ASC")
            items = cursor.fetchall()
        conn.close()
        
        for i in items: view.comboBoxInName.addItem(str(i[0]))
        view.comboBoxInName.blockSignals(False)
        if view.comboBoxInName.count() > 0: view.comboBoxInName.setCurrentIndex(0)
        else: view.comboBoxInName.clearEditText()
        view.filter_spec_combo(view.comboBoxInName.currentText())

    def filter_spec_combo(self, item_name):
        view = self.view
        view.comboBoxInSpec.blockSignals(True); view.comboBoxInSpec.clear() 
        discipline = view.comboBoxInDiscipline.currentText().strip()
        item_name = item_name.strip()
        if not item_name:
            view.comboBoxInSpec.blockSignals(False); view.comboBoxInSpec.clearEditText(); return

        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT spec FROM inbound_ledger WHERE discipline = %s AND item_name = %s AND spec IS NOT NULL AND spec != '' ORDER BY spec ASC", (discipline, item_name))
        specs = cursor.fetchall()
        if not specs:
            cursor.execute("SELECT DISTINCT spec FROM material_items WHERE item_name = %s AND spec IS NOT NULL AND spec != '' ORDER BY spec ASC", (item_name,))
            specs = cursor.fetchall()
        conn.close()
        
        for s in specs: view.comboBoxInSpec.addItem(str(s[0]))
        view.comboBoxInSpec.blockSignals(False)
        if view.comboBoxInSpec.count() > 0: view.comboBoxInSpec.setCurrentIndex(0)
        else: view.comboBoxInSpec.clearEditText()

    # 🌟 [기능 확장] 메인 테이블 그리드 출력 로직 (조회 모드 추가 분기 반영)
    def table_display_in(self, mode="all", p1=None, p2=None):
        self.view.tableWidgetInIn.setRowCount(0)
        self.view.tableWidgetInIn.setSortingEnabled(False)
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # 모드별 조건절 분기
        if mode == "range":
            query = """
                SELECT in_date, discipline, item_name, spec, qty, unit_price, total_price, supplier, remarks, photo1, photo2, photo3, worker, id 
                FROM inbound_ledger 
                WHERE in_date BETWEEN %s AND %s
                ORDER BY in_date DESC, id DESC
            """
            cursor.execute(query, (p1, p2))
        elif mode == "month":
            query = """
                SELECT in_date, discipline, item_name, spec, qty, unit_price, total_price, supplier, remarks, photo1, photo2, photo3, worker, id 
                FROM inbound_ledger 
                WHERE in_date LIKE %s
                ORDER BY in_date DESC, id DESC
            """
            cursor.execute(query, (p1,))
        else:
            # 전체 조회 기본 모드
            query = """
                SELECT in_date, discipline, item_name, spec, qty, unit_price, total_price, supplier, remarks, photo1, photo2, photo3, worker, id 
                FROM inbound_ledger 
                ORDER BY id DESC
            """
            cursor.execute(query)
            
        rows = cursor.fetchall()
        conn.close()
        
        for row_idx, row_data in enumerate(rows):
            self.view.tableWidgetInIn.insertRow(row_idx)
            bg_color = QColor(245, 247, 250) if (row_idx % 4) in [2, 3] else QColor(255, 255, 255)
            for col_idx, value in enumerate(row_data[:-1]):
                if col_idx in [4, 5, 6]: 
                    formatted_val = f"{value:,}" if isinstance(value, (int, float)) else str(value)
                    item = QTableWidgetItem(formatted_val)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg_color)
                self.view.tableWidgetInIn.setItem(row_idx, col_idx, item)
            self.view.tableWidgetInIn.item(row_idx, 0).setData(Qt.UserRole + 1, row_data[-1])
                
        self.view.tableWidgetInIn.setSortingEnabled(True)
        self.view.tableWidgetInIn.resizeColumnsToContents()
        for col in range(self.view.tableWidgetInIn.columnCount()):
            self.view.tableWidgetInIn.setColumnWidth(col, self.view.tableWidgetInIn.columnWidth(col) + 25)

    def show_photo_preview_from_table(self, row, column):
        view = self.view
        for i in range(3):
            item = view.tableWidgetInIn.item(row, 9 + i)
            file_name = item.text().strip() if item else ""
            if file_name and file_name != "None" and "img_" in file_name:
                full_path = os.path.join(view.image_dir, file_name)
                if os.path.exists(full_path):
                    pixmap = QPixmap(full_path)
                    if not pixmap.isNull():
                        scaled_p = pixmap.scaled(view.lbl_previews[i].width(), view.lbl_previews[i].height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        view.lbl_previews[i].setPixmap(scaled_p)
                        view.lbl_previews[i].setStyleSheet("border: 1px solid #4CAF50; background-color: #FFFFFF;")
                        continue
            view.lbl_previews[i].clear(); view.lbl_previews[i].setText(f"사진 {i+1} 없음")
            view.lbl_previews[i].setStyleSheet("border: 1px dashed #BDBDBD; background-color: #FAFAFA; color: #9E9E9E; font-size: 11px;")

    def delete_selected_row(self):
        view = self.view
        current_row = view.tableWidgetInIn.currentRow()
        if current_row < 0: QMessageBox.warning(view, "삭제 오류", "삭제할 항목을 선택해 주세요."); return
        if QMessageBox.question(view, '확인', '선택한 내역을 삭제하시겠습니까?', QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            row_id = view.tableWidgetInIn.item(current_row, 0).data(Qt.UserRole + 1)
            if not row_id: QMessageBox.critical(view, "삭제 실패", "고유 ID를 식별할 수 없습니다."); return

            photos_to_delete = []
            for i in range(3):
                p_item = view.tableWidgetInIn.item(current_row, 9 + i)
                if p_item and p_item.text().strip() and "img_" in p_item.text():
                    photos_to_delete.append(p_item.text().strip())
            try:
                conn = database.get_db_connection(); cursor = conn.cursor()
                cursor.execute("DELETE FROM inbound_ledger WHERE id=%s", (row_id,)); conn.commit(); conn.close()
                for p_name in photos_to_delete:
                    target = os.path.join(view.image_dir, p_name)
                    if os.path.exists(target): os.remove(target)
                QMessageBox.information(view, "삭제 완료", "데이터와 연결된 현장 사진이 파기되었습니다.")
                view.clear_input_fields(); view.table_display_in()
            except Exception as e: QMessageBox.critical(view, "삭제 실패", f"DB 삭제 오류: {e}")

    def export_to_excel(self):
        view = self.view
        row_count, column_count = view.tableWidgetInIn.rowCount(), view.tableWidgetInIn.columnCount()
        if row_count == 0: QMessageBox.warning(view, "추출 실패", "엑셀로 내보낼 데이터가 없습니다."); return
        file_path, _ = QFileDialog.getSaveFileName(view, "엑셀 파일 저장", "자재입고현황_레포트.xlsx", "Excel Files (*.xlsx)")
        if not file_path: return 

        try:
            headers = [view.tableWidgetInIn.horizontalHeaderItem(c).text() for c in range(column_count)]
            table_data = []
            for r in range(row_count):
                row_data = []
                for c in range(column_count):
                    item = view.tableWidgetInIn.item(r, c); val = item.text() if item else ""
                    if c in [4, 5, 6]: val = val.replace(",", ""); val = int(val) if val.isdigit() else 0
                    row_data.append(val)
                table_data.append(row_data)
                
            df = pd.DataFrame(table_data, columns=headers)
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name="입고내역_Report")
                worksheet = writer.sheets["입고내역_Report"]
                for col in worksheet.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    worksheet.column_dimensions[col[0].column_letter].width = max(max_len + 3, 12)
            QMessageBox.information(view, "추출 완료", "성공적으로 엑셀 레포트가 생성되었습니다.")
        except Exception as e: QMessageBox.critical(view, "시스템 에러", f"엑셀 변환 중 오류: {e}")