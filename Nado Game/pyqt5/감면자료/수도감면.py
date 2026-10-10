import sys
import os
import re
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QGroupBox, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt

import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

class WaterCalcApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_paths()
        self.init_ui()

    def init_paths(self):
        now = datetime.now()
        yyyymm = now.strftime("%Y") + now.strftime("%m") + '월'
        yyyy = now.strftime("%Y")
        
        self.detail_file_path = f'D:/과장/1 1 부과자료/{yyyy}년/{yyyymm}/수도감면자료/2609_수도요금 감면세대 상세조회.xlsx'
        self.template_file_path = f'D:/과장/1 1 부과자료/{yyyy}년/Templates/Water_Template_File_for_XPERP_upload.xls'
        self.code_table_path = f'D:/과장/1 1 부과자료/{yyyy}년/Templates/xperp_code_comparasion_table.xlsx'
        self.save_dir_path = f'D:/과장/1 1 부과자료/{yyyy}년/{yyyymm}/xperp_감면자료'

    def init_ui(self):
        self.setWindowTitle('래미안개포루체하임아파트 세대 수도감면 관리 프로그램')
        self.resize(900, 730)
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # 타이틀 라벨
        self.label_title = QLabel('래미안개포루체하임아파트 세대 수도감면 관리 프로그램', central_widget)
        self.label_title.setGeometry(100, 10, 700, 50)
        font_title = self.label_title.font()
        font_title.setFamily('HY헤드라인M')
        font_title.setPointSize(15)
        self.label_title.setFont(font_title)
        self.label_title.setAlignment(Qt.AlignCenter)
        self.label_title.setFrameShape(QLabel.Panel)
        self.label_title.setLineWidth(4)

        # 1. 수도요금 감면세대 상세조회 파일 선택
        self.gb_file1 = QGroupBox('수도요금 감면세대 상세조회 파일 선택', central_widget)
        self.gb_file1.setGeometry(30, 75, 841, 80)
        self.le_file1 = QLineEdit(self.detail_file_path, self.gb_file1)
        self.le_file1.setGeometry(10, 30, 700, 31)
        self.btn_file1 = QPushButton('상세조회파일', self.gb_file1)
        self.btn_file1.setGeometry(720, 30, 110, 31)
        self.btn_file1.clicked.connect(self.select_detail_file)

        # 2. Template 파일 선택
        self.gb_file2 = QGroupBox('XPERP Upload용 Template 파일 선택', central_widget)
        self.gb_file2.setGeometry(30, 165, 841, 80)
        self.le_file2 = QLineEdit(self.template_file_path, self.gb_file2)
        self.le_file2.setGeometry(10, 30, 700, 31)
        self.btn_file2 = QPushButton('Template', self.gb_file2)
        self.btn_file2.setGeometry(720, 30, 110, 31)
        self.btn_file2.clicked.connect(self.select_template_file)

        # 3. 수도용 코드 조견표 파일
        self.gb_file3 = QGroupBox('수도용 코드 조견표 파일', central_widget)
        self.gb_file3.setGeometry(30, 255, 841, 80)
        self.le_file3 = QLineEdit(self.code_table_path, self.gb_file3)
        self.le_file3.setGeometry(10, 30, 700, 31)
        self.btn_file3 = QPushButton('Code Table', self.gb_file3)
        self.btn_file3.setGeometry(720, 30, 110, 31)
        self.btn_file3.clicked.connect(self.select_code_file)

        # 4. XPERP 할인자료 저장경로
        self.gb_file4 = QGroupBox('XPERP 할인자료 업로드파일 저장경로', central_widget)
        self.gb_file4.setGeometry(30, 345, 841, 80)
        self.le_file4 = QLineEdit(self.save_dir_path, self.gb_file4)
        self.le_file4.setGeometry(10, 30, 700, 31)
        self.btn_file4 = QPushButton('저장경로', self.gb_file4)
        self.btn_file4.setGeometry(720, 30, 110, 31)
        self.btn_file4.clicked.connect(self.select_save_dir)

        # 5. 공제 종류별 총 공제요금 합계액 현황표
        self.gb_summary = QGroupBox('공제 종류별 총 공제요금 합계액 현황표', central_widget)
        self.gb_summary.setGeometry(30, 435, 841, 120)
        
        labels_info = [
            ('다자녀감면', 15, 30, 80, 25), ('le_dajanya', 100, 30, 160, 30),
            ('기초생활', 280, 30, 80, 25), ('le_kicho', 360, 30, 160, 30),
            ('중증장애인', 540, 30, 80, 25), ('le_jungjoong', 620, 30, 160, 30),
            ('유공자감면', 15, 75, 80, 25), ('le_yugong', 100, 75, 160, 30),
            ('중복할인', 280, 75, 80, 25), ('le_overlap', 360, 75, 160, 30),
            ('총 합 계', 540, 75, 80, 25), ('le_total', 620, 75, 160, 30)
        ]
        
        self.summary_inputs = {}
        for item in labels_info:
            name, x, y, w, h = item
            if name.startswith('le_'):
                le = QLineEdit(self.gb_summary)
                le.setGeometry(x, y, w, h)
                le.setReadOnly(True)
                self.summary_inputs[name] = le
            else:
                lbl = QLabel(name, self.gb_summary)
                lbl.setGeometry(x, y, w, h)

        # 하단 버튼 및 정보
        self.lbl_developer = QLabel('프로그램 작성 : 임훈택 Rev 1.6, 2026.10 Issued', central_widget)
        self.lbl_developer.setGeometry(30, 665, 350, 30)

        self.btn_verify = QPushButton('자료 검증', central_widget)
        self.btn_verify.setGeometry(380, 660, 140, 40)
        self.btn_verify.clicked.connect(lambda: QMessageBox.information(self, "안내", "계산 시작을 통해 검증이 반영됩니다."))

        self.btn_start = QPushButton('계산 시작', central_widget)
        self.btn_start.setGeometry(530, 660, 160, 40)
        self.btn_start.setStyleSheet("font-weight: bold; color: blue;")
        self.btn_start.clicked.connect(self.start_calculation)

        self.btn_close = QPushButton('종     료', central_widget)
        self.btn_close.setGeometry(700, 660, 160, 40)
        self.btn_close.clicked.connect(self.close)

    def select_detail_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, '상세조회 파일 선택', '', 'Excel Files (*.xlsx *.xls)')
        if fname: self.le_file1.setText(fname)

    def select_template_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Template 파일 선택', '', 'Excel Files (*.xlsx *.xls)')
        if fname: self.le_file2.setText(fname)

    def select_code_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, '코드 조견표 파일 선택', '', 'Excel Files (*.xlsx *.xls)')
        if fname: self.le_file3.setText(fname)

    def select_save_dir(self):
        dname = QFileDialog.getExistingDirectory(self, '저장 경로 선택')
        if dname: self.le_file4.setText(dname)

    def load_water_code_mapping(self, code_file):
        """조견표 파일의 하단 수도 감면 영역(D21~D25 범위, 0-indexed 행 20~24)만 정확히 읽어옴"""
        df = pd.read_excel(code_file, sheet_name=0, header=None)
        mapping = {}
        for idx in range(20, min(25, len(df))):
            row = df.iloc[idx]
            val_cat = row.iloc[2]  # 종류 (기초생활, 다자녀, 유공자, 중증장애, 중복할인1)
            val_code = row.iloc[3] # 코드 (3, I, 2, T, V)
            if pd.notna(val_cat) and pd.notna(val_code):
                mapping[str(val_cat).strip()] = str(val_code).strip()
        print(f"[DEBUG 수도 조견표 매핑]: {mapping}")
        return mapping

    def get_mapped_code(self, cat_name, code_mapping):
        """상세조회 파일의 감면 카테고리명을 정확히 매칭"""
        cat_str = str(cat_name)
        if '기초생활' in cat_str:
            return code_mapping.get('기초생활', '3')
        elif '다자녀' in cat_str:
            return code_mapping.get('다자녀', 'I')
        elif '독립유공' in cat_str or '유공자' in cat_str:
            return code_mapping.get('유공자', '2')
        elif '중증장애' in cat_str:
            return code_mapping.get('중증장애', 'T')
        return ''

    def start_calculation(self):
        f1 = self.le_file1.text()
        f2 = self.le_file2.text()
        f3 = self.le_file3.text()
        f4 = self.le_file4.text()

        if not os.path.exists(f1) or not os.path.exists(f2) or not os.path.exists(f3):
            QMessageBox.warning(self, "경고", "지정한 엑셀 파일 경로 중 존재하지 않는 파일이 있습니다.")
            return

        try:
            code_mapping = self.load_water_code_mapping(f3)

            df_detail_parsed, summary_stats = self.parse_detail_file(f1)
            
            # UI 현황표 업데이트 (양수 값 표시)
            self.summary_inputs['le_dajanya'].setText(f"{summary_stats.get('다자녀감면', 0):>10,}")
            self.summary_inputs['le_kicho'].setText(f"{summary_stats.get('복지감면2 (기초생활수급자)', 0):>10,}")
            self.summary_inputs['le_jungjoong'].setText(f"{summary_stats.get('복지감면3 (중증장애인)', 0):>10,}")
            self.summary_inputs['le_yugong'].setText(f"{summary_stats.get('복지감면1 (독립유공자)', 0):>10,}")
            self.summary_inputs['le_overlap'].setText(f"{summary_stats.get('중복', 0):>10,}")
            self.summary_inputs['le_total'].setText(f"{summary_stats.get('총합', 0):>10,}")

            self.apply_to_template(f2, f4, df_detail_parsed, code_mapping)

            QMessageBox.information(self, "완료", "수도감면 계산 및 업로드 파일 생성이 성공적으로 완료되었습니다!")

        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            print(f"[ERROR 상세]:\n{err_msg}")
            QMessageBox.critical(self, "에러 발생", f"처리 중 오류가 발생했습니다:\n{str(e)}")

    def parse_detail_file(self, detail_file):
        import openpyxl
        wb = openpyxl.load_workbook(detail_file, data_only=True)
        ws = wb.active

        summary_stats = {}
        summary_units = {}
        
        for c in range(2, 7):
            cat = ws.cell(row=4, column=c).value
            amt_str = ws.cell(row=5, column=c).value
            cnt_str = ws.cell(row=6, column=c).value
            if cat:
                cat_clean = str(cat).replace('\n', ' ')
                amt_cleaned = re.sub(r'[^0-9]', '', str(amt_str)) if amt_str else '0'
                amt = int(amt_cleaned) if amt_cleaned else 0
                
                cnt = int(re.sub(r'[^0-9]', '', str(cnt_str))) if cnt_str else 0
                unit_amt = int(amt / cnt) if cnt > 0 else 0
                
                summary_stats[cat_clean] = amt
                summary_units[cat_clean] = unit_amt

        all_records = []
        current_row = 8
        while current_row <= ws.max_row:
            val = ws.cell(row=current_row, column=1).value
            if val and '□' in str(val) and '감면현황' in str(val):
                match_cat = re.search(r'□\s*(.*?)\s*감면현황', str(val))
                current_cat = match_cat.group(1).strip() if match_cat else ""
                
                data_row = current_row + 3
                while data_row <= ws.max_row:
                    r_val = ws.cell(row=data_row, column=1).value
                    if r_val is None or ('□' in str(r_val)):
                        break
                    
                    detail_text = ws.cell(row=data_row, column=3).value
                    if detail_text:
                        matches = re.findall(r'(\d+)[동\-]?\s*(\d+)호?', str(detail_text))
                        if matches:
                            dong_str, ho_str = matches[0]
                            unit_amt = summary_units.get(current_cat, 0)
                            all_records.append({
                                '동': int(dong_str),
                                '호': int(ho_str),
                                '감면구분': current_cat,
                                '세대당금액': unit_amt
                            })
                    data_row += 1
                current_row = data_row
            else:
                current_row += 1

        df_records = pd.DataFrame(all_records)
        total_sum = sum([v for v in summary_stats.values()])
        summary_stats['총합'] = total_sum
        summary_stats['중복'] = 0

        return df_records, summary_stats

    def apply_to_template(self, template_file, save_dir, df_detail, code_mapping):
        df_template = pd.read_excel(template_file, skiprows=0)
        
        if '동' not in df_template.columns or '호' not in df_template.columns:
            raise ValueError("Template 파일에 '동' 또는 '호' 컬럼이 존재하지 않습니다.")

        df_template['동'] = pd.to_numeric(df_template['동'], errors='coerce').fillna(0).astype(int)
        df_template['호'] = pd.to_numeric(df_template['호'], errors='coerce').fillna(0).astype(int)
        
        if not df_detail.empty:
            df_detail['동'] = pd.to_numeric(df_detail['동'], errors='coerce').fillna(0).astype(int)
            df_detail['호'] = pd.to_numeric(df_detail['호'], errors='coerce').fillna(0).astype(int)

            grouped_records = []
            for (dong, ho), group in df_detail.groupby(['동', '호']):
                cats = group['감면구분'].tolist()
                codes = []
                unit_amounts = []
                for cat in cats:
                    code = self.get_mapped_code(cat, code_mapping)
                    if code: codes.append(code)
                    unit_amt = group.loc[group['감면구분'] == cat, '세대당금액'].values[0] if len(group.loc[group['감면구분'] == cat, '세대당금액'].values) > 0 else 0
                    unit_amounts.append(unit_amt)

                final_code = code_mapping.get('중복할인1', 'V') if len(codes) > 1 else (codes[0] if len(codes) == 1 else '')
                total_unit_amt = sum(unit_amounts)

                grouped_records.append({
                    '동': dong,
                    '호': ho,
                    '감면구분': final_code,
                    '수도감면금': total_unit_amt if total_unit_amt != 0 else 0
                })
            df_mapped = pd.DataFrame(grouped_records)
        else:
            df_mapped = pd.DataFrame(columns=['동', '호', '감면구분', '수도감면금'])

        if '감면구분' in df_template.columns:
            df_template.drop(columns=['감면구분'], inplace=True, errors='ignore')
        if '수도감면금' in df_template.columns:
            df_template.drop(columns=['수도감면금'], inplace=True, errors='ignore')

        merged_df = pd.merge(df_template, df_mapped, how='left', on=['동', '호'])
        
        if '수도감면금' in merged_df.columns:
            merged_df['수도감면금'] = pd.to_numeric(merged_df['수도감면금'], errors='coerce').fillna(0)
            
        if '감면구분' in merged_df.columns:
            merged_df['감면구분'] = merged_df['감면구분'].fillna('')

        for col in merged_df.columns:
            if col != '수도감면금':
                merged_df[col] = merged_df[col].fillna('')

        now = datetime.now()
        dt_str = now.strftime("%Y") + now.strftime("%m")
        file_name = dt_str + 'WATER_XPERP_Upload_i_columns.xlsx'
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        save_path = os.path.join(save_dir, file_name)
        merged_df.to_excel(save_path, index=False, header=False)
        return save_path

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WaterCalcApp()
    window.show()
    sys.exit(app.exec_())