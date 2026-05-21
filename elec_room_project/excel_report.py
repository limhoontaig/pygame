import sqlite3
import shutil
import os
import zipfile
import re
from datetime import datetime, timedelta
import openpyxl
from db_manager import DB_NAME, DATA_LABELS

def clean_external_links_physically(file_path):
    """
    오류 팝업의 근본 원인인 엑셀 내부의 외부 링크 구조(externalLinks)를
    Zipfile 레벨에서 물리적으로 완전히 분해하여 박멸합니다.
    """
    temp_file_path = file_path + ".tmp"
    try:
        with zipfile.ZipFile(file_path, 'r') as zin:
            with zipfile.ZipFile(temp_file_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    filename = item.filename
                    
                    # 1) externalLinks 폴더와 내부 xml 파일 전체 제거
                    if "externalLinks/" in filename:
                        continue
                        
                    # 2) 통합 문서 관계망 정의 파일 내외부 링크 선언 구문 삭제
                    if filename == "xl/_rels/workbook.xml.rels":
                        data = zin.read(filename).decode('utf-8')
                        # externalLink 관련 Relationship 태그 원천 삭제
                        data_clean = re.sub(r'<Relationship[^>]*Type="[^"]*externalLink"[^>]*/>', '', data)
                        zout.writestr(filename, data_clean.encode('utf-8'))
                        continue
                        
                    # 3) 전체 구조 선언 파일에서 externalReferences 태그 부분 들어내기
                    if filename == "xl/workbook.xml":
                        data = zin.read(filename).decode('utf-8')
                        data_clean = re.sub(r'<externalReferences>.*?</externalReferences>', '', data, flags=re.DOTALL)
                        zout.writestr(filename, data_clean.encode('utf-8'))
                        continue
                        
                    # 나머지 안전한 파일들은 그대로 복사
                    zout.writestr(item, zin.read(filename))
                    
        os.remove(file_path)
        os.rename(temp_file_path, file_path)
    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        print(f"[경고] 외부 링크 물리 청소 중 예외 발생 (작동에는 영향 없음): {e}")

def generate_excel_report(selected_date):
    """
    오류 로그 발생을 원천 차단하고 상하단 테이블 분리 구조에 맞추어
    24시간 실측 통합 데이터를 완벽히 조율해 안착시킵니다.
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    template_file = os.path.join(BASE_DIR, "template_전기실_운영일지.xlsx")
    output_file = os.path.join(BASE_DIR, f"{selected_date}_전기실_운영일지.xlsx")
    
    if not os.path.exists(template_file):
        raise FileNotFoundError(f"템플릿 파일 [{template_file}]을 찾을 수 없습니다.")
    
    # 1. 원본 서식 복사 및 로드
    shutil.copy(template_file, output_file)
    wb = openpyxl.load_workbook(output_file, data_only=False)
    
    # 코드단 캐시 초기화 기법 적용
    if hasattr(wb, 'external_link_refs'): wb.external_link_refs = []
    if hasattr(wb, '_external_links'): wb._external_links = []

    # 날짜 서식 가공
    dt = datetime.strptime(selected_date, "%Y-%m-%d")
    date_str_formatted = f"{dt.year}년 {dt.month:02d}월 {dt.day:02d}일"
    
    # 2. 시트 탐색 및 고유 이름 설정 변경
    ws_summary = None
    ws_detail = None
    for sheet in wb.worksheets:
        if "운영현황" in sheet.title:
            ws_summary = sheet
            sheet.title = f"{selected_date}_전력설비_운영현황"
        elif "상세내역" in sheet.title:
            ws_detail = sheet
            sheet.title = f"{selected_date}_상세내역"
            
    if not ws_summary: ws_summary = wb.worksheets[0]
    if not ws_detail: ws_detail = wb.worksheets[1] if len(wb.worksheets) > 1 else wb.worksheets[0]

    # DB 핸들러 연결
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # =========================================================================
    # [시트 1] 전력설비_운영현황 분석 처리
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
                val_strip = cell.value.strip().replace(" ", "")
                if "일시:" in val_strip or ("일시" in val_strip and ":" in val_strip):
                    cell.value = f"일시 : {date_str_formatted}"
                elif "max(" in val_strip:
                    label = cell.value.split('"')[1].strip() if '"' in cell.value else cell.value.replace("max(", "").replace(")", "").strip()
                    cell.value = extremes_dict.get(("MAX", label), "-")
                elif "min(" in val_strip:
                    label = cell.value.split('"')[1].strip() if '"' in cell.value else cell.value.replace("min(", "").replace(")", "").strip()
                    cell.value = extremes_dict.get(("MIN", label), "-")

    # 한전 메인 적산 사용량 연동 구역
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
    # [시트 2] 상세내역 데이터 입력 (상단/하단 격리 추적 매핑)
    # =========================================================================
    for row in ws_detail.iter_rows(max_row=3):
        for cell in row:
            if cell.value and isinstance(cell.value, str) and "일자" in cell.value:
                cell.value = f"일자 : {date_str_formatted}"

    # 시간대별(0~23시) DB 원데이터 추출 취합
    avg_selects = ", ".join([f'AVG("{name}")' for name in DATA_LABELS])
    c.execute(f'SELECT CAST(strftime("%H", log_time) AS INTEGER) as hour, {avg_selects} FROM raw_data WHERE log_date = ? GROUP BY hour', (selected_date,))
    hourly_rows = c.fetchall()
    
    hourly_data = {}
    for r in hourly_rows:
        hour = r[0]
        for idx, label in enumerate(DATA_LABELS):
            if r[idx + 1] is not None:
                hourly_data[(hour, label)] = round(r[idx + 1], 1)

    # 💡 중간 노이즈 행에 막히지 않도록 상세내역 모든 행을 완전 탐색하여 '0'을 개별 식별
    for row_idx, row in enumerate(ws_detail.iter_rows(min_row=4, max_row=60), start=4):
        first_cell_val = str(row[0].value).strip() if row[0].value is not None else ""
        
        # 상단 또는 하단 테이블의 "0"시 시작점 감지
        if first_cell_val == "0":
            # 해당 행에 포함된 모든 열들의 필드 서식 파싱 및 기억
            col_mapping = {}
            for col_idx, cell in enumerate(row):
                if cell.value and isinstance(cell.value, str):
                    clean_label = cell.value.strip().replace('"', '')
                    if clean_label in DATA_LABELS:
                        col_mapping[col_idx] = clean_label
            
            # 매핑 정의가 성립된 열이 있으면, 즉시 아래로 24개 행에 걸쳐 시간별 수직 주입 진행
            if col_mapping:
                for h in range(24):
                    target_row = row_idx + h
                    # 시간 셀 값 고정 보정
                    ws_detail.cell(row=target_row, column=1).value = h
                    # 필드 맞춤 값 주입
                    for col_idx, label in col_mapping.items():
                        val = hourly_data.get((h, label), "-")
                        ws_detail.cell(row=target_row, column=col_idx + 1).value = val

    # 연결 자원 종료 및 디스크 보관
    conn.close()
    wb.save(output_file)
    
    # 💥 [핵심 보완] 물리 압축 패키징 강제 정밀 세척 프로세스 가동
    clean_external_links_physically(output_file)
    print(f"보고서 결함 완벽 수정 및 출력 성공: {output_file}")

if __name__ == "__main__":
    generate_excel_report("2026-05-21")