import sqlite3
import shutil
import os
from datetime import datetime, timedelta
import openpyxl
from db_manager import DB_NAME, DATA_LABELS

def generate_excel_report(selected_date):
    """
    선택된 날짜(selected_date: 'YYYY-MM-DD')의 데이터를 기반으로
    템플릿 엑셀 파일을 읽어와 데이터를 채운 후 새 파일로 저장합니다.
    """
    # 스크립트 파일 위치 기준 절대 경로 설정 (파일 미인식 에러 방지)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    template_file = os.path.join(BASE_DIR, "template_전기실_운영일지.xlsx")
    output_file = os.path.join(BASE_DIR, f"{selected_date}_전기실_운영일지.xlsx")
    
    if not os.path.exists(template_file):
        raise FileNotFoundError(f"템플릿 파일 [{template_file}]을 찾을 수 없습니다. 경로를 확인해 주세요.")
    
    # 1. 템플릿 파일을 복사하여 결과 파일 생성 후 로드
    shutil.copy(template_file, output_file)
    wb = openpyxl.load_workbook(output_file)
    
    # DB 연결 및 데이터 가져오기
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 날짜 포맷 변환 (예: '2026-05-21' -> '2026년 05월 21일')
    dt = datetime.strptime(selected_date, "%Y-%m-%d")
    date_str_formatted = f"{dt.year}년 {dt.month:02d}월 {dt.day:02d}일"
    
    # =========================================================================
    # [시트 1] 전력설비_운영현황 (요약 및 통계 시트)
    # =========================================================================
    # 템플릿의 실제 시트명에 맞추어 변수 설정 (혹시 시트명이 다르면 엑셀에 맞게 수정 가능)
    sheet_summary_name = "20260521_전력설비_운영현황"
    if sheet_summary_name not in wb.sheetnames:
        # 시트 이름이 다를 경우 첫 번째 시트를 기본으로 선택하도록 안전장치 추가
        ws_summary = wb.worksheets[0]
    else:
        ws_summary = wb[sheet_summary_name]
    
    # daily_extremes 테이블에서 해당 날짜의 MAX, MIN 행 전체 가져오기
    c.execute('SELECT * FROM daily_extremes WHERE log_date = ?', (selected_date,))
    rows_extreme = c.fetchall()
    
    # 컬럼명 리스트 확보를 통해 데이터 인덱스 매핑 준비
    c.execute('PRAGMA table_info(daily_extremes)')
    columns_extreme = [col[1] for col in c.fetchall()]
    
    # extremes_dict[(extreme_type, col_name)] = value 구조로 파싱
    extremes_dict = {}
    for r in rows_extreme:
        ext_type = r[columns_extreme.index('extreme_type')]
        for col_name in DATA_LABELS:
            if col_name in columns_extreme:
                val = r[columns_extreme.index(col_name)]
                extremes_dict[(ext_type, col_name)] = round(val, 1) if val is not None else "-"

    # 템플릿 내 날짜 바인딩 및 통계 필드 채우기
    for row in ws_summary.iter_rows():
        for cell in row:
            if cell.value and isinstance(cell.value, str):
                val_strip = cell.value.strip()
                
                # 1) 일시/날짜 영역 업데이트
                if "일시 :" in val_strip:
                    cell.value = f"일시 : {date_str_formatted}"
                
                # 2) 최고값 매핑 (예: max( "KEP_V_R") 또는 max("KEP_V_R"))
                elif val_strip.startswith('max('):
                    label = val_strip.split('"')[1].strip() if '"' in val_strip else val_strip.replace("max(", "").replace(")", "").strip()
                    cell.value = extremes_dict.get(("MAX", label), "-")
                
                # 3) 최저값 매핑 (예: min( "KEP_V_R"))
                elif val_strip.startswith('min('):
                    label = val_strip.split('"')[1].strip() if '"' in val_strip else val_strip.replace("min(", "").replace(")", "").strip()
                    cell.value = extremes_dict.get(("MIN", label), "-")

    # 4) 전력량계 적산 현황 요약 데이터 매핑 (한전 메인 누적 전력량)
    today_mwh = "-"
    c.execute('SELECT MAX(KEP_P_kWh) FROM raw_data WHERE log_date = ?', (selected_date,))
    res_today = c.fetchone()
    if res_today and res_today[0] is not None:
        today_mwh = round(res_today[0], 1)
        
    prev_date = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
    prev_mwh = "-"
    c.execute('SELECT MAX(KEP_P_kWh) FROM raw_data WHERE log_date = ?', (prev_date,))
    res_prev = c.fetchone()
    if res_prev and res_prev[0] is not None:
        prev_mwh = round(res_prev[0], 1)
        
    diff_mwh = round(today_mwh - prev_mwh, 1) if today_mwh != "-" and prev_mwh != "-" else "-"

    for row in ws_summary.iter_rows():
        for cell in row:
            if cell.value and isinstance(cell.value, str):
                val_strip = cell.value.strip()
                if val_strip == "1469.79":      # 템플릿 예시 데이터 대체 (금일 지침)
                    cell.value = today_mwh
                elif val_strip == "1464.06":    # 전일 지침
                    cell.value = prev_mwh
                elif val_strip == "5.7300000000000182": # 사용량 차이
                    cell.value = diff_mwh


    # =========================================================================
    # [시트 2] 상세내역 (24시간 시간별 데이터 시트)
    # =========================================================================
    sheet_detail_name = "20260521_상세내역"
    if sheet_detail_name not in wb.sheetnames:
        ws_detail = wb.worksheets[1] if len(wb.worksheets) > 1 else wb.worksheets[0]
    else:
        ws_detail = wb[sheet_detail_name]
    
    # 1) 일자 업데이트
    for row in ws_detail.iter_rows(max_row=5):
        for cell in row:
            if cell.value and isinstance(cell.value, str) and "일자 :" in cell.value:
                cell.value = f"일자 : {date_str_formatted}"

    # 2) 각 데이터 필드의 시간별(0~23시) 평균 구하기
    # 동적 쿼리 생성: AVG("실내온도"), AVG("외기온도")... 형태
    avg_selects = ", ".join([f'AVG("{name}")' for name in DATA_LABELS])
    query = f"""
        SELECT CAST(strftime('%H', log_time) AS INTEGER) as hour, {avg_selects}
        FROM raw_data 
        WHERE log_date = ? 
        GROUP BY hour
    """
    c.execute(query, (selected_date,))
    hourly_rows = c.fetchall()
    
    # hourly_data[(hour, label)] = value 구조로 캐싱
    hourly_data = {}
    for r in hourly_rows:
        hour = r[0]
        for idx, label in enumerate(DATA_LABELS):
            val = r[idx + 1]
            if val is not None:
                hourly_data[(hour, label)] = round(val, 1)

    # 3) 템플릿의 데이터 입력 구역 순회하며 값 채우기
    for row in ws_detail.iter_rows(min_row=4):
        # 첫 번째 열에 있는 시간 정보 추출 (0~23시 값인지 확인)
        time_cell_val = row[0].value
        if time_cell_val is None:
            continue
            
        try:
            current_hour = int(float(str(time_cell_val).strip()))
        except ValueError:
            continue
            
        if current_hour < 0 or current_hour > 23:
            continue
            
        # 해당 시간 행의 셀들을 돌면서 필드명 매핑 텍스트 치환
        for cell in row[1:]:
            if cell.value and isinstance(cell.value, str):
                label_candidate = cell.value.strip()
                if (current_hour, label_candidate) in hourly_data:
                    cell.value = hourly_data[(current_hour, label_candidate)]
                elif label_candidate in DATA_LABELS:
                    cell.value = "-" # 데이터가 없는 빈 시간대는 하이픈 처리

    # 저장 및 연결 종료
    wb.save(output_file)
    conn.close()
    print(f"보고서 생성 성공: {output_file}")

if __name__ == "__main__":
    # 테스트 실행
    generate_excel_report("2026-05-21")