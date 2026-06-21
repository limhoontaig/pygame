# usage_event_handler.py
import database

class UsageEventHandler:
    def __init__(self, parent_tab):
        self.tab = parent_tab

    def get_calculated_floor_text(self):
        ho_text = self.tab.comboHo.currentText().strip()
        if ho_text.isdigit() and len(ho_text) >= 3:
            return f"{ho_text[:-2]}층 복도 작업"
        return "(호수 입력 필요)"

    def update_floor_corridor_logic(self):
        if self.tab.is_loading_row:
            return
        if self.tab.chkFloorCorridor.isChecked():
            self.tab.comboType.setCurrentText("공용")
            floor_text = self.get_calculated_floor_text()
            self.tab.lblFloorStatus.setText(f"➔ {floor_text}" if floor_text != "(호수 입력 필요)" else "➔ (호수 입력 필요)")
        else:
            self.tab.lblFloorStatus.setText("")

    def handle_type_change(self, current_type):
        if self.tab.is_loading_row: return
        self.tab.comboDong.blockSignals(True)
        self.tab.comboDong.clear()
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT dong FROM dongho_master ORDER BY CAST(dong AS INTEGER) ASC, dong ASC")
        dongs = [str(d[0]) for d in cursor.fetchall()]
        conn.close()
        
        for d in dongs: self.tab.comboDong.addItem(d)
            
        if current_type == "공용":
            if "999" not in dongs: self.tab.comboDong.addItem("999")
            self.tab.comboDong.blockSignals(False)
            self.tab.comboDong.setCurrentText("999") 
            self.handle_dong_change("999")
        else:
            index = self.tab.comboDong.findText("101")
            self.tab.comboDong.blockSignals(False)
            self.tab.comboDong.setCurrentIndex(index if index >= 0 else 0)
            self.handle_dong_change(self.tab.comboDong.currentText())

    def handle_dong_change(self, selected_dong):
        if not selected_dong or self.tab.is_loading_row: return
        self.sync_ho_combo(selected_dong)
        
        if selected_dong == "999":
            self.tab.comboDiscipline.blockSignals(True)
            self.tab.comboDiscipline.clear()
            for i in range(self.tab.comboHo.count()): self.tab.comboDiscipline.addItem(self.tab.comboHo.itemText(i))
            self.tab.comboDiscipline.blockSignals(False)
            
            if self.tab.comboHo.count() > 0:
                first_ho = self.tab.comboHo.itemText(0)
                self.tab.comboDiscipline.setCurrentText(first_ho)
                self.sync_items_by_discipline(first_ho)
        else:
            self.tab.comboDiscipline.blockSignals(True)
            self.tab.comboDiscipline.clear()
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT discipline FROM inbound_ledger WHERE discipline IS NOT NULL AND discipline != '' ORDER BY discipline ASC")
            for disp in cursor.fetchall(): self.tab.comboDiscipline.addItem(str(disp[0]))
            conn.close()
            self.tab.comboDiscipline.blockSignals(False)
            if self.tab.comboDiscipline.count() > 0:
                self.tab.comboDiscipline.setCurrentIndex(0)
                self.sync_items_by_discipline(self.tab.comboDiscipline.currentText())

    def handle_ho_change(self, selected_ho):
        if not selected_ho or self.tab.is_loading_row or self.tab.is_syncing_ho_disp: return
        if self.tab.comboType.currentText() == "공용" and self.tab.comboDong.currentText() == "999":
            self.tab.is_syncing_ho_disp = True
            self.tab.comboDiscipline.setCurrentText(selected_ho)
            self.tab.is_syncing_ho_disp = False
            self.sync_items_by_discipline(selected_ho)

    def handle_discipline_change(self, selected_disp):
        if not selected_disp or self.tab.is_loading_row or self.tab.is_syncing_ho_disp: return
        if self.tab.comboType.currentText() == "공용" and self.tab.comboDong.currentText() == "999":
            self.tab.is_syncing_ho_disp = True
            self.tab.comboHo.setCurrentText(selected_disp)
            self.tab.is_syncing_ho_disp = False
        self.sync_items_by_discipline(selected_disp)

    def sync_ho_combo(self, selected_dong):
        if not selected_dong or self.tab.is_loading_row: return
        self.tab.comboHo.blockSignals(True)
        self.tab.comboHo.clear()
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ho FROM dongho_master WHERE dong = %s ORDER BY CAST(ho AS INTEGER) ASC, ho ASC", (selected_dong,))
        for h in cursor.fetchall(): self.tab.comboHo.addItem(str(h[0]))
        conn.close()
        if self.tab.comboHo.count() > 0: self.tab.comboHo.setCurrentIndex(0)
        self.tab.comboHo.blockSignals(False)

    def sync_items_by_discipline(self, discipline):
        if self.tab.is_loading_row or not discipline: return
        self.tab.CB_Item.blockSignals(True)
        self.tab.CB_Item.clear()
        conn = database.get_db_connection()
        cursor = conn.cursor()
        if "복도 작업" in discipline:
            cursor.execute("SELECT DISTINCT item_name FROM inbound_ledger ORDER BY item_name ASC")
        else:
            cursor.execute("SELECT DISTINCT item_name FROM inbound_ledger WHERE discipline = %s ORDER BY item_name ASC", (discipline,))
        for i in cursor.fetchall(): self.tab.CB_Item.addItem(str(i[0]))
        conn.close()
        self.tab.CB_Item.blockSignals(False)
        self.handle_item_change(self.tab.CB_Item.currentText())

    def handle_item_change(self, item_name):
        if self.tab.is_loading_row or not item_name:
            self.tab.LE_CurrentStock.clear()
            return
        self.sync_specs_by_item(item_name)
        self.tab.update_stock_display()

    def sync_specs_by_item(self, item_name):
        if not item_name or self.tab.is_loading_row: return
        self.tab.CB_Spec.blockSignals(True)
        self.tab.CB_Spec.clear()
        conn = database.get_db_connection()
        cursor = conn.cursor()
        if "복도 작업" in self.tab.comboDiscipline.currentText():
            cursor.execute("SELECT DISTINCT spec FROM inbound_ledger WHERE item_name = %s ORDER BY spec ASC", (item_name,))
        else:
            cursor.execute("SELECT DISTINCT spec FROM inbound_ledger WHERE discipline = %s AND item_name = %s ORDER BY spec ASC", (self.tab.comboDiscipline.currentText(), item_name))
        for s in cursor.fetchall(): self.tab.CB_Spec.addItem(str(s[0]))
        conn.close()
        self.tab.CB_Spec.blockSignals(False)