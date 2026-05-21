import sqlite3
import shutil
import os
from datetime import datetime, timedelta
import openpyxl
from db_manager import DB_NAME, DATA_LABELS

def generate_excel_report(selected_date):
    """
    선택된 날짜(selected_date: 'YYYY-MM-DD')의 데이터를 기반으로
    템플릿 서식을 100% 유지한 채 시트명을 변경하고 데이터를 채워 저장합니다.
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    template_file = os.path.join(BASE_DIR, "template_전기실_운영일지.xlsx")
    
    # 출력 파일명 형식 예시: '2026-05-21_전기실_운영일지.xlsx'
    output_file = os.path.join(BASE_DIR, f"{selected_date}_전기실_운영일지.xlsx")
    
    if not os.path.exists(template_file):
        raise FileNotFoundError(f"템플릿 파일 [{template_file}]을 찾을 수 없습니다.")
    
    # 1. 원본 서식 파일 안전 복사 및 로드
    shutil.copy(template_file, output_file)
    wb = openpyxl.load_workbook(output_file, data_only=False)
    
    # 유령 외부 수식 링크 제거 (엑셀 열 때 '복구된 레코드' 에러 원천 차단)
    if hasattr(wb, 'external_link_refs'):
        wb.external_link_refs = []

    # 날짜 문자열 포맷 변환
    dt = datetime.strptime(selected_date, "%Y-%m-%d")
    date_str_formatted = f"{dt.year}년 {dt.month:02d}월 {dt.day:02d}일"
    date_prefix = selected_date  # 시트 이름 앞에 붙을 '2026-05-21'
    
    # 2. 시트 이름 변경 ("작성년월일_+전력설비_운영현황" 규칙 적용)
    ws_summary = None
    ws_detail = None
    
    for sheet in wb.worksheets:
        if "운영현황" in sheet.title:
            ws_summary = sheet
            sheet.title = f"{date_prefix}_전력설비_운영현황"
        elif "상세내역" in sheet.title:
            ws_detail = sheet
            sheet.title = f"{date_prefix}_상세내역"
            
    if not ws_summary: ws_summary = wb.worksheets[0]
    if not ws_detail: ws_detail = wb.worksheets[1] if len(wb.worksheets) > 1 else wb.worksheets[0]

    # DB 연결
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # =========================================================================
    # [시트 1] 전력설비_운영현황 데이터 입력
    # =========================================================================
    c.execute('SELECT * FROM daily_extremes WHERE log_date = ?', (selected_date,))
    rows_extreme = c.fetchall()
    c.execute('PRAGMA table_info(daily_extremes)')
    columns_extreme = [col[1] for col in c.fetchall()]
    
    extremes_dict = {}
    for r in rows_extreme:
        ext_type = r[columns_extreme.index('extreme_type')]
        for col_name in DATA_LABELS:
            if col_name in columns_extreme:
                val = r[columns_extreme.index(col_name)]
                extremes_dict[(ext_type, col_name)] = round(val, 1) if val is not None else "-"

    for row in ws_summary.iter_rows():
        for cell in row:
            if cell.value and isinstance(cell.value, str):
                val_strip = cell.value.strip().replace(" ", "") # 공백 제거 비교
                
                if "일시:" in val_strip or "일시" in val_strip and ":" in val_strip:
                    cell.value = f"일시 : {date_str_formatted}"
                elif "max(" in val_strip:
                    label = cell.value.split('"')[1].strip() if '"' in cell.value else cell.value.replace("max(", "").replace(")", "").strip()
                    cell.value = extremes_dict.get(("MAX", label), "-")
                elif "min(" in val_strip:
                    label = cell.value.split('"')[1].strip() if '"' in cell.value else cell.value.replace("min(", "").replace(")", "").strip()
                    cell.value = extremes_dict.get(("MIN", label), "-")

    # 전력량계 적산 현황 요약 데이터 치환
    today_mwh = "-"
    c.execute('SELECT MAX(KEP_P_kWh) FROM raw_data WHERE log_date = ?', (selected_date,))
    res_today = c.fetchone()
    if res_today and res_today[0] is not None: today_mwh = round(res_today[0], 1)
        
    prev_date = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
    prev_mwh = "-"
    c.execute('SELECT MAX(KEP_P_kWh) FROM raw_data WHERE log_date = ?', (prev_date,))
    res_prev = c.fetchone()
    if res_prev and res_prev[0] is not None: prev_mwh = round(res_prev[0], 1)
        
    diff_mwh = round(today_mwh - prev_mwh, 1) if today_mwh != "-" and prev_mwh != "-" else "-"

    for row in ws_summary.iter_rows():
        for cell in row:
            if cell.value and isinstance(cell.value, str):
                val_strip = cell.value.strip()
                if val_strip == "1469.79": cell.value = today_mwh
                elif val_strip == "1464.06": cell.value = prev_mwh
                elif val_strip == "5.7300000000000182": cell.value = diff_mwh

    # =========================================================================
    # [시트 2] 상세내역 24시간 데이터 입력 (0시 행을 기반으로 수직 자동 채우기)
    # =========================================================================
    # 상단 일자 텍스트 수정
    for row in ws_detail.iter_rows(max_row=3):
        for cell in row:
            if cell.value and isinstance(cell.value, str) and "일자" in cell.value:
                cell.value = f"일자 : {date_str_formatted}"

    # 시간별(0~23시) 평균 DB 데이터 캐싱
    avg_selects = ", ".join([f'AVG("{name}")' for name in DATA_LABELS])
    c.execute(f'SELECT CAST(strftime("%H", log_time) AS INTEGER) as hour, {avg_selects} FROM raw_data WHERE log_date = ? GROUP BY hour', (selected_date,))
    hourly_rows = c.fetchall()
    
    hourly_data = {}
    for r in hourly_rows:
        hour = r[0]
        for idx, label in enumerate(DATA_LABELS):
            if r[idx + 1] is not None:
                hourly_data[(hour, label)] = round(r[idx + 1], 1)

    # 💡 0시 행을 찾아 각 열이 어떤 DB 필드명(DATA_LABELS)에 해당치 매핑 맵 매칭 수행
    col_mapping = {}  # {열번호: "필드명"}
    mapping_row_idx = None
    
    for row_idx, row in enumerate(ws_detail.iter_rows(min_row=4, max_row=15), start=4):
        if row[0].value is not None and str(row[0].value).strip() == "0":
            mapping_row_idx = row_idx
            for col_idx, cell in enumerate(row):
                if cell.value and isinstance(cell.value, str):
                    clean_label = cell.value.strip().replace('"', '')
                    if clean_label in DATA_LABELS:
                        col_mapping[col_idx] = clean_label
            break

    # 매핑 인덱스를 기준으로 0시부터 23시까지 하향식으로 셀 데이터 주입 (기존 결재란/선 스타일 유지)
    if mapping_row_idx:
        start_row = mapping_row_idx
        for current_hour in range(24):
            target_row_idx = start_row + current_hour
            
            # 첫 열 시간 값 강제 적용
            ws_detail.cell(row=target_row_idx, column=1).value = current_hour
            
            # 매핑된 열에 데이터 채우기
            for col_idx, label in col_mapping.items():
                val = hourly_data.get((current_hour, label), "-")
                ws_detail.cell(row=target_row_idx, column=col_idx + 1).value = val

    # 저장 및 연결 종료
    wb.save(output_file)
    conn.close()
    print(f"보고서 최종 생성 완료: {output_file}")

if __name__ == "__main__":
    generate_excel_report("2026-05-21")