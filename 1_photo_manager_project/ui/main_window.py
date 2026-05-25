# ui/main_window.py
import sys
import os
import pathlib
import webbrowser

# 실행 경로 보완 (어디서 실행하든 패키지를 정상적으로 찾을 수 있도록 설정)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QSplitter, QTabWidget, QTreeView, QTableWidget, 
                             QTableWidgetItem, QLabel, QPushButton, QLineEdit, 
                             QCheckBox, QGroupBox, QStatusBar, QApplication, 
                             QAbstractItemView, QComboBox)
from PyQt5.QtCore import Qt, QSize

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("공간·시간 중심 미디어 데이터베이스 및 편집 스튜디오 (Photo DB)")
        self.resize(1440, 900) # 편집 및 지도 기능을 고려해 넓고 시원한 스튜디오 규격 설정

        # 메인 중앙 위젯 및 전체 가로 레이아웃
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # 마우스 드래그로 각 창의 너비 조절이 가능한 메인 스플리터 (3단 분할 레이아웃)
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.main_splitter)

        # 3단 구조 배치 함수 순차 호출
        self.init_left_panel()   # 1단: 좌측 타임라인 내비게이션
        self.init_center_panel() # 2단: 중앙 다목적 탭 작업 영역 (편집 / 조회 / 자동분류)
        self.init_right_panel()  # 3단: 우측 프리뷰 및 GPS/메타데이터 속성 창

        # 하단 상태바 세팅
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("새 레이아웃 구성 완료 - 시스템 준비 완료")

    # -------------------------------------------------------------------------
    # [1단] 좌측 레이아웃: 트리뷰 영역 (년도별/월별 타임라인 탐색창)
    # -------------------------------------------------------------------------
    def init_left_panel(self):
        from PyQt5.QtWidgets import QSizePolicy

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        group_box = QGroupBox("타임라인 탐색 (디렉터리 DB)")
        group_layout = QVBoxLayout(group_box)

        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        
        # [핵심 추가] 트리뷰가 늘어나고 줄어드는 것을 방해하지 않도록 정책 설정
        self.tree_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        group_layout.addWidget(self.tree_view)
        left_layout.addWidget(group_box)

        # [핵심 추가] 좌측 판넬 위젯 전체도 좌우로 유연하게 작동하도록 설정
        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 스플리터에 추가
        self.main_splitter.addWidget(left_widget)

    # -------------------------------------------------------------------------
    # [2단] 중앙 레이아웃: 탭 위젯 영역 (편집 스튜디오 / 조회 화면 / 자동 분류)
    # -------------------------------------------------------------------------
    # ui/main_window.py 내의 init_center_panel 메서드를 아래 내용으로 교체합니다.

    def init_center_panel(self):
        from PyQt5.QtWidgets import QDateEdit, QSizePolicy
        from PyQt5.QtCore import QDate
        from PyQt5.QtGui import QFont

        self.center_tab = QTabWidget()
        self.center_tab.setMovable(True)
        
        # ---------------------------------------------------------------------
        # --- [탭 1] 이미지 편집 및 변환 스튜디오 (기존 구조 유지) ---
        # ---------------------------------------------------------------------
        tab_edit_widget = QWidget()
        tab_edit_layout = QVBoxLayout(tab_edit_widget)
        target_group = QGroupBox("편집 대상 이미지")
        target_layout = QHBoxLayout(target_group)
        self.edit_target_path = QLineEdit(); self.edit_target_path.setPlaceholderText("오른쪽 프리뷰에서 선택하거나, 파일을 열어주세요...")
        self.btn_load_edit = QPushButton("파일 열기")
        target_layout.addWidget(self.edit_target_path); target_layout.addWidget(self.btn_load_edit)
        tab_edit_layout.addWidget(target_group)
        self.edit_canvas_label = QLabel("편집할 이미지를 선택하거나 열어주세요.")
        self.edit_canvas_label.setAlignment(Qt.AlignCenter); self.edit_canvas_label.setStyleSheet("background-color: #000000; color: #ffffff; border: 1px solid #333333;"); self.edit_canvas_label.setMinimumSize(QSize(640, 480))
        tab_edit_layout.addWidget(self.edit_canvas_label, 1)
        tools_group = QGroupBox("이미지 편집 툴박스 (OpenCV 엔진)"); tools_layout = QHBoxLayout(tools_group)
        tool_resize_gb = QGroupBox("해상도/포맷 변환"); resize_layout = QVBoxLayout(tool_resize_gb)
        self.combo_resize = QComboBox(); self.combo_resize.addItems(["원본 유지", "Full HD (1920x1080)", "HD (1280x720)", "모바일용 (800x600)"])
        self.combo_format = QComboBox(); self.combo_format.addItems(["포맷 유지", "JPG (고압축)", "PNG (투명도)", "BMP (무압축)"])
        resize_layout.addWidget(QLabel("크기 조절:")); resize_layout.addWidget(self.combo_resize); resize_layout.addWidget(QLabel("포맷 변환:")); resize_layout.addWidget(self.combo_format)
        tool_roi_gb = QGroupBox("부분 복사/크롭 (ROI)"); roi_layout = QVBoxLayout(tool_roi_gb)
        self.btn_roi_select = QPushButton("부분 선택 (드래그)"); self.btn_roi_crop = QPushButton("선택 영역 크롭"); self.btn_roi_copy = QPushButton("선택 영역 복사")
        roi_layout.addWidget(self.btn_roi_select); roi_layout.addWidget(self.btn_roi_crop); roi_layout.addWidget(self.btn_roi_copy)
        tool_filter_gb = QGroupBox("회전 및 필터"); filter_layout = QVBoxLayout(tool_filter_gb)
        self.btn_rotate = QPushButton("90도 회전"); self.btn_filter = QPushButton("그레이스케일 필터")
        filter_layout.addWidget(self.btn_rotate); filter_layout.addWidget(self.btn_filter)
        self.btn_save_edit = QPushButton("💾 편집본\n저장하기"); self.btn_save_edit.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;"); self.btn_save_edit.setMinimumSize(QSize(100, 90))
        tools_layout.addWidget(tool_resize_gb); tools_layout.addWidget(tool_roi_gb); tools_layout.addWidget(tool_filter_gb); tools_layout.addWidget(self.btn_save_edit)
        tab_edit_layout.addWidget(tools_group)
        self.center_tab.addTab(tab_edit_widget, "이미지 편집 Studio")

        # ---------------------------------------------------------------------
        # --- [탭 2] 파일 관리 및 사진 조회 화면 (간격 최적화 정돈 버전) ---
        # ---------------------------------------------------------------------
        tab_view_widget = QWidget()
        tab_view_layout = QVBoxLayout(tab_view_widget)

        # 검색 필터 전체를 감싸는 그룹박스
        filter_group = QGroupBox("데이터베이스 정밀 통합 검색")
        
        # 전체 가로 레이아웃 (왼쪽: 3줄 조건 / 오른쪽: 버튼)
        filter_main_layout = QHBoxLayout(filter_group)
        filter_main_layout.setContentsMargins(15, 10, 15, 12)
        
        # [핵심 변경] 왼쪽 조건 입력창들을 쌓을 세로 레이아웃 (요청하신 줄간 스페이스 10 강제 지정)
        inputs_v_layout = QVBoxLayout()
        inputs_v_layout.setSpacing(10) 

        # 날짜 가시성용 폰트
        large_font = QFont()
        large_font.setPointSize(11)
        large_font.setBold(True)

        # --- [1번째 줄] 촬영 기간 설정 ---
        row1_layout = QHBoxLayout()
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy - MM - dd")
        self.date_from.setDate(QDate.currentDate().addYears(-1))
        self.date_from.setMinimumSize(QSize(140, 32))
        self.date_from.setFont(large_font)
        self.date_from.setStyleSheet("color: #2b5fdf; padding-left: 5px;")

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy - MM - dd")
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setMinimumSize(QSize(140, 32))
        self.date_to.setFont(large_font)
        self.date_to.setStyleSheet("color: #2b5fdf; padding-left: 5px;")

        lbl_date = QLabel("📅 촬영 기간 설정 :")
        lbl_date.setMinimumWidth(120)
        
        row1_layout.addWidget(lbl_date)
        row1_layout.addWidget(self.date_from)
        row1_layout.addWidget(QLabel(" ~ "))
        row1_layout.addWidget(self.date_to)
        row1_layout.addStretch()

        # --- [2번째 줄] 활동명 검색 영역 ---
        row2_layout = QHBoxLayout()
        self.search_act_input = QLineEdit()
        self.search_act_input.setPlaceholderText("검색할 활동명(Activity) 키워드를 입력하세요...")
        self.search_act_input.setMinimumHeight(30)
        self.check_act_wild = QCheckBox("단어 포함")
        
        lbl_act = QLabel("🏷️ 활동명 검색 :")
        lbl_act.setMinimumWidth(120)

        row2_layout.addWidget(lbl_act)
        row2_layout.addWidget(self.search_act_input, 1)
        row2_layout.addWidget(self.check_act_wild)

        # --- [3번째 줄] 파일명 검색 영역 ---
        row3_layout = QHBoxLayout()
        self.search_file_input = QLineEdit()
        self.search_file_input.setPlaceholderText("검색할 파일명 키워드를 입력하세요...")
        self.search_file_input.setMinimumHeight(30)
        self.check_file_wild = QCheckBox("단어 포함")
        
        lbl_file = QLabel("📁 파일명 검색 :")
        lbl_file.setMinimumWidth(120)

        row3_layout.addWidget(lbl_file)
        row3_layout.addWidget(self.search_file_input, 1)
        row3_layout.addWidget(self.check_file_wild)

        # 3개의 줄을 왼쪽 세로 레이아웃에 배치
        inputs_v_layout.addLayout(row1_layout)
        inputs_v_layout.addLayout(row2_layout)
        inputs_v_layout.addLayout(row3_layout)

        # --- [오른쪽 배치] 높이가 과하게 늘어나지 않도록 조정한 우측 버튼 ---
        self.btn_search = QPushButton("🔍조건\n조회 실행")
        self.btn_search.setFont(large_font)
        self.btn_search.setStyleSheet("""
            QPushButton {
                background-color: #2b5fdf; 
                color: white; 
                border-radius: 6px;
                font-size: 11pt;

                padding-top: 10px;    /* 글자 위쪽 여백 10픽셀 */
                padding-bottom: 10px; /* 글자 아래쪽 여백 10픽셀 */
                padding-left: 5px;   /* 글자 좌측 여백 */
                padding-right: 5px;  /* 글자 우측 여백 */
            }
            QPushButton:hover {
                background-color: #1e4bb8;
            }
        """)
        self.btn_search.setFixedWidth(180)
        # [핵심 변경] 버튼의 높이가 왼쪽 3줄 레이아웃을 억지로 찢지 않도록 최대 높이를 고정 제한
        self.btn_search.setMaximumHeight(175) 

        # 가로 레이아웃에 최종 배치 후 남는 여백 방지 조치
        filter_main_layout.addLayout(inputs_v_layout, 1)
        filter_main_layout.addWidget(self.btn_search, 0, Qt.AlignVCenter) # 세로 중앙 정렬 배치
        
        tab_view_layout.addWidget(filter_group)

        # 조회 결과 테이블 위젯 (기존 유지)
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["파일명", "활동명(Activity)", "파일 용량", "촬영/생성일시"])
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tab_view_layout.addWidget(self.table_widget)

        self.center_tab.addTab(tab_view_widget, "파일 관리 및 사진 보기")

        # ---------------------------------------------------------------------
        # --- [탭 3] 일자별 자동 분류 대시보드 (기존 구조 유지) ---
        # ---------------------------------------------------------------------
        tab_sync_widget = QWidget(); tab_sync_layout = QVBoxLayout(tab_sync_widget)
        sync_group = QGroupBox("구글 포토 및 PC 파편화 파일 통합 일자별 자동 정렬"); sync_layout = QVBoxLayout(sync_group)
        src_lay = QHBoxLayout(); self.edit_src_path = QLineEdit(); self.btn_select_src = QPushButton("원본 폴더 선택")
        src_lay.addWidget(QLabel("원본 저장소:")); src_lay.addWidget(self.edit_src_path); src_lay.addWidget(self.btn_select_src)
        dest_lay = QHBoxLayout(); self.edit_dest_path = QLineEdit(); self.btn_select_dest = QPushButton("목적지 선택")
        dest_lay.addWidget(QLabel("백업 목적지:")); dest_lay.addWidget(self.edit_dest_path); dest_lay.addWidget(self.btn_select_dest)
        btn_lay = QHBoxLayout(); self.btn_run_classify = QPushButton("⚡ 일자별 자동 정렬 및 DB 구축 시작"); self.btn_run_classify.setMinimumHeight(45); self.btn_run_classify.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;"); self.btn_close = QPushButton("종  료"); self.btn_close.setMinimumHeight(45); btn_lay.addWidget(self.btn_run_classify, 3); btn_lay.addWidget(self.btn_close, 1)
        sync_group.setLayout(sync_layout); sync_layout.addLayout(src_lay); sync_layout.addLayout(dest_lay); sync_layout.addLayout(btn_lay); tab_sync_layout.addWidget(sync_group); tab_sync_layout.addStretch()
        self.center_tab.addTab(tab_sync_widget, "날짜별 정리 대시보드")

        self.main_splitter.addWidget(self.center_tab)

    # -------------------------------------------------------------------------
    # [3단] 우측 레이아웃: 프리뷰(미리보기) 및 [GPS 위치 / 메타데이터 속성창]
    # -------------------------------------------------------------------------

    def init_right_panel(self):
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # [핵심 변경] 우측 판넬 내부에서 상하(Vertical)로 드래그 조절이 가능한 스플리터 생성
        self.right_sub_splitter = QSplitter(Qt.Vertical)
        right_layout.addWidget(self.right_sub_splitter)

        # ----------------------------------------------------
        # 1. 상부: 미디어 프리뷰 모니터 영역
        # ----------------------------------------------------
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 5) # 하단 여백 최소화

        preview_group = QGroupBox("미디어 프리뷰 (미리보기)")
        preview_group_layout = QVBoxLayout(preview_group)

        self.media_viewer_label = QLabel("사진/영상을 선택하면\n여기에 표시됩니다.")
        self.media_viewer_label.setAlignment(Qt.AlignCenter)
        self.media_viewer_label.setStyleSheet("background-color: #1e1e1e; color: #8c8c8c; border-radius: 5px;")
        # 최소 크기를 대폭 낮춰서 사용자가 위로 끝까지 올릴 수도 있도록 유연성 부여
        self.media_viewer_label.setMinimumSize(QSize(240, 180)) 
        preview_group_layout.addWidget(self.media_viewer_label, 1) # 사진 창이 가득 차도록 가중치 부여

        # 재생 및 슬라이드 제어바
        playback_layout = QHBoxLayout()
        self.btn_prev = QPushButton("◀ 이전")
        self.btn_slide = QPushButton("▶ 슬라이드 쇼")
        self.btn_next = QPushButton("다음 ▶")
        playback_layout.addWidget(self.btn_prev)
        playback_layout.addWidget(self.btn_slide)
        playback_layout.addWidget(self.btn_next)
        preview_group_layout.addLayout(playback_layout)
        
        preview_layout.addWidget(preview_group)
        self.right_sub_splitter.addWidget(preview_container) # 상부 위젯 등록

        # ----------------------------------------------------
        # 2. 하부: 메타데이터 및 GPS 정보 편집창 영역
        # ----------------------------------------------------
        meta_container = QWidget()
        meta_layout = QVBoxLayout(meta_group_container := QGroupBox("선택된 사진 정보 및 공간 데이터 관리"))
        meta_container_layout = QVBoxLayout(meta_container)
        meta_container_layout.setContentsMargins(0, 5, 0, 0)
        meta_container_layout.addWidget(meta_group_container)

        self.edit_meta_filename = QLineEdit()
        self.edit_meta_filename.setReadOnly(True)
        self.edit_meta_actname = QLineEdit()
        
        # GPS 위도/경도 레이아웃
        gps_layout = QHBoxLayout()
        self.edit_meta_lat = QLineEdit(); self.edit_meta_lat.setPlaceholderText("위도 (Latitude)")
        self.edit_meta_lon = QLineEdit(); self.edit_meta_lon.setPlaceholderText("경도 (Longitude)")
        gps_layout.addWidget(self.edit_meta_lat)
        gps_layout.addWidget(self.edit_meta_lon)

        # 구글 지도 연동 버튼
        self.btn_google_map = QPushButton("🌐 구글 지도에서 촬영 장소 보기")
        self.btn_google_map.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
        self.btn_google_map.clicked.connect(self.open_google_map)

        # DB 저장 버튼
        self.btn_save_meta = QPushButton("DB 태그 및 위치 정보 저장")
        self.btn_save_meta.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold;")

        meta_layout.addWidget(QLabel("파 일 명:"))
        meta_layout.addWidget(self.edit_meta_filename)
        meta_layout.addWidget(QLabel("활동명 태그 (Activity):"))
        meta_layout.addWidget(self.edit_meta_actname)
        meta_layout.addWidget(QLabel("촬영 위치 공간 좌표 (GPS):"))
        meta_layout.addLayout(gps_layout)
        meta_layout.addWidget(self.btn_google_map)
        meta_layout.addWidget(self.btn_save_meta)
        meta_layout.addStretch() # 내부 컴포넌트들을 위로 밀착시켜 하단 여백 확보

        self.right_sub_splitter.addWidget(meta_container) # 하부 위젯 등록

        # ----------------------------------------------------
        # 3. 기본 마스터 초기 크기 비율 설정 (상하 균형 조정)
        # ----------------------------------------------------
        # 우측 판넬 전체 높이 중 상부 프리뷰에 70%, 하부 속성창에 30%를 기본 할당합니다.
        self.right_sub_splitter.setSizes([550, 250])

        # 메인 좌-중-우 스플리터에 우측 판넬 최종 등록
        self.main_splitter.addWidget(right_widget)
        
        # ----------------------------------------------------
        # [핵심 변경] 스플리터가 늘어날 때 어느 창이 우선적으로 늘어날지 지정 (Stretch Factor)
        # ----------------------------------------------------
        # 각 인덱스(0:좌, 1:중, 2:우)의 신축 비율을 지정합니다.
        # 좌측(0)과 우측(2)도 마우스로 조절할 때 유연하게 확장될 수 있도록 가중치를 부여합니다.
        self.main_splitter.setStretchFactor(0, 1) # 좌측 판넬 신축성 켬
        self.main_splitter.setStretchFactor(1, 3) # 중앙 판넬 기본 비중을 크게 줌
        self.main_splitter.setStretchFactor(2, 2) # 우측 프리뷰 신축성 켬

        # 프로그램을 처음 켰을 때의 초기 황금 비율 너비 (픽셀 단위)
        self.main_splitter.setSizes([220, 720, 400])

    # -------------------------------------------------------------------------
    # 구글 지도 브라우저 실행 핵심 슬롯 함수
    # -------------------------------------------------------------------------
    def open_google_map(self):
        """오른쪽 위치 입력란의 위도/경도를 파싱하여 외부 기본 웹브라우저로 구글 지도를 호출합니다."""
        lat = self.edit_meta_lat.text().strip()
        lon = self.edit_meta_lon.text().strip()
        
        if not lat or not lon:
            # 팝업 메시지를 MainWindow 컨텍스트에서 안전하게 생성
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "위치 정보 없음", "선택한 사진에 등록된 GPS 공간 좌표 정보가 없습니다.")
            return
            
        # 구글 맵 좌표 검색 표준 인터페이스 URL 매핑
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        webbrowser.open(google_maps_url)

# 단독 테스트 구동용 스크립트 진입점
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())