# ui_graph_manager.py
import sqlite3
import pandas as pd
import os
from datetime import timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QListWidget, QAbstractItemView, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPageLayout
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

import db_manager

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

class GraphManager(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.main_win = parent_window  # 메인 윈도우의 날짜창 등에 접근하기 위한 참조
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # 상단 컨트롤 레이아웃
        graph_ctrl = QHBoxLayout()
        
        # [왼쪽 축] 다중 선택 리스트 위젯
        self.data_selector = QListWidget()
        self.data_selector.setSelectionMode(QAbstractItemView.MultiSelection) 
        self.data_selector.addItems(db_manager.DATA_LABELS)
        self.data_selector.setMaximumHeight(80) 
        
        # [오른쪽 보조축] 다중 선택 리스트 위젯
        self.right_axis_selector = QListWidget()
        self.right_axis_selector.setSelectionMode(QAbstractItemView.MultiSelection)
        self.right_axis_selector.setMaximumHeight(80) 

        self.period_selector = QComboBox()
        self.period_selector.addItems(["일간 (실시간 데이터)", "주간 (시간별 평균)", "월간 (시간별 평균)"])
        
        # 그래프 제어용 버튼 생성
        self.btn_save_graph = QPushButton("📊 그래프 저장")
        self.btn_save_graph.setStyleSheet("background-color: #34495e; color: white; font-weight: bold; min-height: 30px;")
        
        self.btn_print_graph = QPushButton("🖨️ 그래프 인쇄")
        self.btn_print_graph.setStyleSheet("background-color: #16a085; color: white; font-weight: bold; min-height: 30px;")
        
        graph_ctrl.addWidget(QLabel("기본(왼쪽) 축 필드 선택:"))
        graph_ctrl.addWidget(self.data_selector)
        graph_ctrl.addWidget(QLabel("➡️ 오른쪽(보조) 축으로 보낼 필드:")) 
        graph_ctrl.addWidget(self.right_axis_selector)     
        graph_ctrl.addWidget(QLabel("조회 기간:"))
        graph_ctrl.addWidget(self.period_selector)
        graph_ctrl.addWidget(self.btn_save_graph)
        graph_ctrl.addWidget(self.btn_print_graph)
        layout.addLayout(graph_ctrl)

        # 캔버스 배치
        self.canvas = FigureCanvas(Figure(figsize=(8, 5)))
        self.ax = self.canvas.figure.add_subplot(111)
        layout.addWidget(self.canvas)

        # 내부 이벤트 연결
        self.period_selector.currentIndexChanged.connect(self.update_graph)
        self.data_selector.itemSelectionChanged.connect(self.sync_right_axis_list)
        self.right_axis_selector.itemSelectionChanged.connect(self.update_graph)
        self.btn_save_graph.clicked.connect(self.save_graph_to_file)
        self.btn_print_graph.clicked.connect(self.print_graph_canvas)

        # 초기 신호 잠금 및 해제 제어
        self.data_selector.blockSignals(True)
        self.right_axis_selector.blockSignals(True)
        if self.data_selector.count() > 0:
            self.data_selector.item(0).setSelected(True)
        self.data_selector.blockSignals(False)
        self.right_axis_selector.blockSignals(False)

    def sync_right_axis_list(self):
        self.data_selector.blockSignals(True)
        self.right_axis_selector.blockSignals(True)
        try:
            prev_selected = [item.text() for item in self.right_axis_selector.selectedItems()]
            left_selected = [item.text() for item in self.data_selector.selectedItems()]
            
            self.right_axis_selector.clear()
            if left_selected:
                self.right_axis_selector.addItems(left_selected)
                for i in range(self.right_axis_selector.count()):
                    item = self.right_axis_selector.item(i)
                    if item.text() in prev_selected:
                        item.setSelected(True)
        finally:
            self.data_selector.blockSignals(False)
            self.right_axis_selector.blockSignals(False)
        self.update_graph()

    def update_graph(self):
        # 메인 윈도우의 현재 탭 인덱스 확인 (그래프 탭이 아닐 때는 연산 안 함)
        if self.main_win.stack.currentIndex() != 1: return
        
        selected_items = self.data_selector.selectedItems()
        if not selected_items:
            self.canvas.figure.clf()
            self.ax = self.canvas.figure.add_subplot(111)
            self.ax.text(0.5, 0.5, "비교할 필드를 선택해주세요.", ha='center')
            self.canvas.draw()
            return
            
        target_cols = [item.text() for item in selected_items]
        period = self.period_selector.currentText()
        selected_date = self.main_win.qdate.date().toPyDate() # 메인 윈도우 날짜 객체 참조

        right_cols = [item.text() for item in self.right_axis_selector.selectedItems()]
        right_cols = [col for col in right_cols if col in target_cols] 
        left_cols = [col for col in target_cols if col not in right_cols]

        cols_str = ', '.join([f'"{col}"' for col in target_cols])
        
        try:
            conn = sqlite3.connect(db_manager.DB_NAME)
            if "일간" in period:
                query = f'SELECT log_time, {cols_str} FROM raw_data WHERE log_date = ? ORDER BY log_time ASC'
                params = (selected_date.strftime('%Y-%m-%d'),)
            else:
                days = 7 if "주간" in period else 30
                start_date = selected_date - timedelta(days=days)
                query = f'SELECT log_date || \' \' || SUBSTR(log_time,1,5) as dt, {cols_str} FROM hourly_avg WHERE log_date BETWEEN ? AND ? ORDER BY log_date, log_time'
                params = (start_date.strftime('%Y-%m-%d'), selected_date.strftime('%Y-%m-%d'))

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
        except Exception as e:
            print(f"그래프 DB 조회 에러 발생: {e}")
            return

        self.canvas.figure.clf()
        self.ax = self.canvas.figure.add_subplot(111)
        
        if not df.empty:
            x_col = 'log_time' if "일간" in period else 'dt'
            all_lines = []
            
            for col in left_cols:
                if col in df.columns:
                    line = self.ax.plot(df[x_col], df[col], marker='o', markersize=2, label=col)
                    all_lines += line
            
            if left_cols:
                self.ax.set_ylabel(', '.join(left_cols[:2]) + ('...' if len(left_cols) > 2 else ''), color='#1f77b4', fontweight='bold')
                self.ax.tick_params(axis='y', labelcolor='#1f77b4')
            else:
                self.ax.yaxis.set_visible(False)

            if right_cols:
                ax2 = self.ax.twinx()
                for col in right_cols:
                    if col in df.columns:
                        line = ax2.plot(df[x_col], df[col], marker='^', markersize=3, linestyle='--', label=f"{col} (우)")
                        all_lines += line
                
                ax2.set_ylabel(', '.join(right_cols[:2]) + ('...' if len(right_cols) > 2 else ''), color='#ff7f0e', fontweight='bold')
                ax2.tick_params(axis='y', labelcolor='#ff7f0e')
                ax2.grid(False) 

            if all_lines:
                labels = [l.get_label() for l in all_lines]
                self.ax.legend(all_lines, labels, loc='upper right')
                
            self.ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
            self.ax.set_title(f"선택 필드 {period} 분석 (양방향 멀티 축 제어)", fontsize=13, fontweight='bold')
            self.ax.grid(True, linestyle='--')
            self.canvas.figure.autofmt_xdate() 
        else:
            self.ax.text(0.5, 0.5, "데이터가 존재하지 않습니다.", ha='center')
        
        self.canvas.draw()

    def save_graph_to_file(self):
        selected_date = self.main_win.qdate.date().toString("yyyy-MM-dd")
        period = self.period_selector.currentText().split()[0]
        default_filename = f"{selected_date}_{period}_부하분석그래프.png"
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "그래프 이미지 저장", default_filename, "PNG 이미지 (*.png);;JPEG 이미지 (*.jpg);;모든 파일 (*)"
        )
        if filepath:
            try:
                self.canvas.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "저장 완료", f"그래프 이미지가 성공적으로 저장되었습니다.\n\n경로: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "저장 실패", f"그래프 저장 중 오류가 발생했습니다:\n{e}")

    def print_graph_canvas(self):
        # 1. 프린터 객체는 원래대로 고해상도(HighResolution) 모드로 정상 생성합니다.
        printer = QPrinter(QPrinter.HighResolution)
        
        # 2. 아랫줄에서 QPageLayout을 이용하여 가로 방향(Landscape) 설정을 줍니다.
        printer.setPageOrientation(QPageLayout.Landscape) 
        
        # 프린트 대화상자 열기
        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec_() == QPrintDialog.Accepted:
            try:
                from PyQt5.QtGui import QPainter
                painter = QPainter(printer)
                pixmap = self.canvas.grab()
                rect = painter.viewport()
                size = pixmap.size()
                size.scale(rect.size(), Qt.KeepAspectRatio)
                painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
                painter.setWindow(pixmap.rect())
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                QMessageBox.information(self, "인쇄 완료", "프린터로 데이터 전송이 완료되었습니다.")
            except Exception as e:
                QMessageBox.critical(self, "인쇄 실패", f"인쇄 작업 중 오류가 발생했습니다:\n{e}")