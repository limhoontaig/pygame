# usage_data_manager.py
import os
import time
import shutil
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QDate
import common.database as database

class UsageDataManager:
    def __init__(self, parent_tab):
        self.tab = parent_tab

    def process_save(self):
        """사용 내역 등록 및 수정 저장 프로세스"""
        use_date = self.tab.dateEditUse.date().toString("yyyy-MM-dd")
        usage_type = self.tab.comboType.currentText()
        dong = self.tab.comboDong.currentText().strip()
        ho = self.tab.comboHo.currentText().strip()
        discipline = self.tab.comboDiscipline.currentText().strip()
        item_name = self.tab.CB_Item.currentText().strip()
        spec = self.tab.CB_Spec.currentText().strip()
        qty_str = self.tab.lineEditUseQty.text().strip()
        remarks = self.tab.lineEditUseRemarks.text().strip()
        
        if not item_name:
            QMessageBox.warning(self.tab, "입력 오류", "사용할 자재 품명을 선택해 주세요.")
            return
        if not qty_str or not qty_str.isdigit() or int(qty_str) <= 0:
            QMessageBox.warning(self.tab, "입력 오류", "사용 수량은 1개 이상의 숫자로 입력해야 합니다.")
            return
            
        qty = int(qty_str)

        # 복도 체크박스 가동 시 문자열 치환
        if self.tab.chkFloorCorridor.isChecked():
            floor_text = self.tab.event_handler.get_calculated_floor_text()
            if floor_text != "(호수 입력 필요)":
                ho = floor_text
                discipline = floor_text
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        final_photo_names = [None, None, None]
        if self.tab.is_edit_mode:
            cursor.execute("SELECT photo1, photo2, photo3 FROM usage_ledger WHERE id = %s", (self.tab.editing_row_id,))
            old_photos = cursor.fetchone()
            if old_photos:
                final_photo_names = list(old_photos)

        for i in range(3):
            file_src = self.tab.selected_photos[i]
            if file_src:
                if final_photo_names[i]:
                    old_path = os.path.join(self.tab.image_dir, final_photo_names[i])
                    if os.path.exists(old_path): os.remove(old_path)
                
                ext = os.path.splitext(file_src)[1]
                new_filename = f"use_{int(time.time())}_{i+1}{ext}"
                try:
                    shutil.copy(file_src, os.path.join(self.tab.image_dir, new_filename))
                    final_photo_names[i] = new_filename
                except Exception as e:
                    QMessageBox.critical(self.tab, "사진 복사 실패", f"사진 에러: {e}")
            else:
                if self.tab.is_edit_mode and self.tab.photo_widgets[i]["label"].text() == f"사진 {i+1}: 등록되지 않음":
                    if final_photo_names[i]:
                        old_path = os.path.join(self.tab.image_dir, final_photo_names[i])
                        if os.path.exists(old_path): os.remove(old_path)
                        final_photo_names[i] = None

        if self.tab.is_edit_mode:
            cursor.execute("""
                UPDATE usage_ledger 
                SET use_date=%s, usage_type=%s, dong=%s, ho=%s, discipline=%s, item_name=%s, spec=%s, qty=%s, remarks=%s, worker=%s,
                    photo1=%s, photo2=%s, photo3=%s
                WHERE id=%s
            """, (use_date, usage_type, dong, ho, discipline, item_name, spec, qty, remarks, self.tab.current_user,
                  final_photo_names[0], final_photo_names[1], final_photo_names[2], self.tab.editing_row_id))
            QMessageBox.information(self.tab, "수정 완료", "출고 사용 대장이 수정되었습니다.")
        else:
            cursor.execute("""
                INSERT INTO usage_ledger (use_date, usage_type, dong, ho, discipline, item_name, spec, qty, remarks, worker, photo1, photo2, photo3)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (use_date, usage_type, dong, ho, discipline, item_name, spec, qty, remarks, self.tab.current_user,
                  final_photo_names[0], final_photo_names[1], final_photo_names[2]))
            QMessageBox.information(self.tab, "등록 완료", "자재 사용 내역이 대장에 등록되었습니다.")
            
        conn.commit()
        conn.close()
        
        self.tab.clear_usage_fields()
        self.tab.table_display_usage()

    def load_selected_row(self, current_row):
        """테이블 선택 행을 편집 폼으로 역로드"""
        use_date_str = self.tab.tableWidgetUse.item(current_row, 0).text()
        usage_type = self.tab.tableWidgetUse.item(current_row, 1).text()
        dong = self.tab.tableWidgetUse.item(current_row, 2).text()
        ho = self.tab.tableWidgetUse.item(current_row, 3).text()
        discipline = self.tab.tableWidgetUse.item(current_row, 4).text()
        item_name = self.tab.tableWidgetUse.item(current_row, 5).text()
        spec = self.tab.tableWidgetUse.item(current_row, 6).text()
        qty = self.tab.tableWidgetUse.item(current_row, 7).text().replace(",", "")
        remarks = self.tab.tableWidgetUse.item(current_row, 8).text()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, photo1, photo2, photo3 FROM usage_ledger 
            WHERE use_date=%s AND usage_type=%s AND dong=%s AND ho=%s AND item_name=%s AND qty=%s
            ORDER BY id DESC LIMIT 1
        """, (use_date_str, usage_type, dong, ho, item_name, int(qty)))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            self.tab.is_edit_mode = True
            self.tab.editing_row_id = result[0]
            self.tab.is_loading_row = True 
            
            self.tab.dateEditUse.setDate(QDate.fromString(use_date_str, "yyyy-MM-dd"))
            self.tab.comboType.setCurrentText(usage_type)
            self.tab.comboDong.setCurrentText(dong)
            
            if "복도 작업" in ho:
                self.tab.chkFloorCorridor.setChecked(True)
                self.tab.lblFloorStatus.setText(f"➔ {ho}")
                
                self.tab.comboHo.blockSignals(True)
                self.tab.comboHo.clear()
                self.tab.comboHo.addItem(ho)
                self.tab.comboHo.blockSignals(False)
                
                self.tab.comboDiscipline.blockSignals(True)
                self.tab.comboDiscipline.clear()
                self.tab.comboDiscipline.addItem(discipline)
                self.tab.comboDiscipline.blockSignals(False)
            else:
                self.tab.chkFloorCorridor.setChecked(False)
                if usage_type == "공용":
                    self.tab.comboHo.clear()
                    conn = database.get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT ho FROM dongho_master WHERE dong = '999'")
                    for h in cursor.fetchall(): self.tab.comboHo.addItem(str(h[0]))
                    conn.close()
                else:
                    self.tab.event_handler.sync_ho_combo(dong)
                self.tab.comboHo.setCurrentText(ho)
                self.tab.comboDiscipline.setCurrentText(discipline)
            
            self.tab.event_handler.sync_items_by_discipline(discipline)
            self.tab.CB_Item.setCurrentText(item_name)
            self.tab.event_handler.sync_specs_by_item(item_name)
            self.tab.CB_Spec.setCurrentText(spec)
            
            self.tab.lineEditUseQty.setText(qty)
            self.tab.lineEditUseRemarks.setText(remarks)

            self.tab.selected_photos = [None, None, None]
            for i in range(3):
                p_name = result[1 + i]
                if p_name:
                    self.tab.photo_widgets[i]["label"].setText(str(p_name))
                    self.tab.photo_widgets[i]["label"].setStyleSheet("color: #1976D2; font-weight: bold;")
                else:
                    self.tab.photo_widgets[i]["label"].setText(f"사진 {i+1}: 등록되지 않음")
                    self.tab.photo_widgets[i]["label"].setStyleSheet("color: gray;")
            
            self.tab.is_loading_row = False 
            self.tab.update_stock_display()
            
            self.tab.group_box_use.setTitle("⚠️ 자재 사용 내역 수정 모드")
            self.tab.btn_save_use.setText("수정 완료 저장")
            self.tab.btn_save_use.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; height: 35px;")
            self.tab.btn_cancel_use_edit.setVisible(True)

    def delete_row(self, current_row):
        """선택 행 삭제 기능"""
        use_date = self.tab.tableWidgetUse.item(current_row, 0).text()
        dong = self.tab.tableWidgetUse.item(current_row, 2).text()
        ho = self.tab.tableWidgetUse.item(current_row, 3).text()
        item_name = self.tab.tableWidgetUse.item(current_row, 5).text()
        qty = int(self.tab.tableWidgetUse.item(current_row, 7).text().replace(",", ""))
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM usage_ledger 
            WHERE use_date=%s AND dong=%s AND ho=%s AND item_name=%s AND qty=%s
        """, (use_date, dong, ho, item_name, qty))
        conn.commit()
        conn.close()
        
        if self.tab.is_edit_mode: 
            self.tab.clear_usage_fields()
        self.tab.table_display_usage()
        QMessageBox.information(self.tab, "삭제 성공", "선택 정보가 사용 대장에서 정상 제외되었습니다.")