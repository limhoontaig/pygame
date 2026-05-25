# services/file_service.py
import os
import pathlib
import numpy as np
import cv2
from PIL import Image
from PIL.ExifTags import TAGS
from PyQt5.QtGui import QImage, QPixmap

import shutil
from datetime import datetime

class FileService:
    def __init__(self):
        pass

    def imread_korean(self, filename, flags=cv2.IMREAD_COLOR, dtype=np.uint8):
        """한글 경로 파일도 에러 없이 읽을 수 있도록 우회하는 함수"""
        try:
            n = np.fromfile(filename, dtype)
            img = cv2.imdecode(n, flags)
            return img
        except Exception as e:
            print(f"이미지 읽기 실패: {e}")
            return None

    def read_exif(self, file_path):
        """사진 파일의 EXIF 메타데이터에서 촬영 일시(DateTime)를 추출합니다."""
        try:
            image = Image.open(file_path)
            info = image._getexif()
            if not info:
                return None
                
            exif_data = {}
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                exif_data[decoded] = value
                
            # 촬영 날짜 반환 (없으면 수정 날짜 등으로 대체하거나 None)
            return exif_data.get('DateTimeOriginal') or exif_data.get('DateTime')
        except Exception:
            return None

    def calculate_scale(self, img_w, img_h, target_w=640, target_h=480):
        """라벨 크기에 맞춰 이미지를 비율 유지하며 조정할 스케일 비율 계산"""
        if img_w <= target_w and img_h <= target_h:
            return 1.0, "normal"
            
        w_ratio = target_w / img_w
        h_ratio = target_h / img_h
        
        if w_ratio < h_ratio:
            return w_ratio, "width"
        else:
            return h_ratio, "height"

    def convert_cv_to_pixmap(self, cv_img, target_width=None, target_height=None):
        """OpenCV의 BGR 이미지를 PyQt에서 쓸 수 있는 QPixmap으로 변환"""
        if cv_img is None:
            return QPixmap()
            
        h, w, ch = cv_img.shape
        bytes_per_line = ch * w
        qt_img = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_BGR888)
        pixmap = QPixmap.fromImage(qt_img)
        
        if target_width and target_height:
            return pixmap.scaled(target_width, target_height, aspectRatioMode=1) # 지종 비율 유지
        return pixmap

    # services/file_service.py에 아래 내용을 추가/업데이트합니다.

    def get_media_creation_date(self, file_path):
        """사진 EXIF나 동영상 파일 자체 속성에서 최선의 촬영/생성 날짜를 추출합니다."""
        ext = pathlib.Path(file_path).suffix.lower()
        
        # 1. 사진 파일인 경우 EXIF 추출 시도
        if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            exif_date = self.read_exif(file_path)
            if exif_date:
                try:
                    # 보통 'YYYY:MM:DD HH:MM:SS' 형식으로 들어옵니다.
                    return datetime.strptime(exif_date[:10], '%Y:%m:%d').strftime('%Y-%m-%d')
                except Exception:
                    pass

        # 2. 동영상 파일이거나 EXIF 데이터가 없는 사진인 경우 OS 생성/수정일 활용
        # 구글 테이크아웃 파일은 간혹 메타데이터가 깨지므로 파일 수정 시간(mtime)이 대안이 됩니다.
        try:
            timestamp = os.path.getmtime(file_path)
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        except Exception:
            return "Unknown_Date"

    def classify_and_move_files(self, source_dir, target_base_dir, progress_callback=None):
        """
        source_dir 안의 모든 사진/영상을 읽어 
        target_base_dir 하위에 YYYY/MM-DD 폴더 구조를 만들어 복사(또는 이동)합니다.
        """
        if not os.path.exists(source_dir) or not os.path.exists(target_base_dir):
            return False, "경로가 존재하지 않습니다."

        supported_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.mp4', '.avi', '.mov', '.mkv')
        
        # 처리할 파일 목록 수집
        file_list = []
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.lower().endswith(supported_exts):
                    file_list.append(os.path.join(root, file))

        total_files = len(file_list)
        if total_files == 0:
            return False, "분류할 이미지나 동영상 파일이 없습니다."

        success_count = 0
        
        for idx, src_file_path in enumerate(file_list):
            try:
                # 1. 날짜 추출 (예: '2026-05-25')
                date_str = self.get_media_creation_date(src_file_path)
                
                if date_str != "Unknown_Date":
                    year = date_str[:4]       # '2026'
                    month_day = date_str[5:]   # '05-25'
                    # 목적지 폴더 구조 생성: target_base_dir/2026/05-25/
                    dest_dir = os.path.join(target_base_dir, year, month_day)
                else:
                    dest_dir = os.path.join(target_base_dir, "Unknown_Date")

                os.makedirs(dest_dir, exist_ok=True)
                
                # 2. 파일 복사 (구글 포토 원본과 PC 파일 유실 방지를 위해 일단 copy로 진행 안전)
                file_name = os.path.basename(src_file_path)
                dest_file_path = os.path.join(dest_dir, file_name)
                
                # 동일 이름 파일이 대상 폴더에 이미 존재할 경우 이름 뒤에 언더바(_) 추가하여 덮어쓰기 방지
                base, extension = os.path.splitext(file_name)
                counter = 1
                while os.path.exists(dest_file_path):
                    new_file_name = f"{base}_{counter}{extension}"
                    dest_file_path = os.path.join(dest_dir, new_file_name)
                    counter += 1

                shutil.copy2(src_file_path, dest_file_path) # 메타데이터 보존하며 복사
                success_count += 1
                
                # UI에 현재 진행 상황 전달 (Progress 바 연동용)
                if progress_callback:
                    progress_callback(idx + 1, total_files)
                    
            except Exception as e:
                print(f"파일 처리 중 에러 발생 ({src_file_path}): {e}")

        return True, f"총 {total_files}개 중 {success_count}개 파일 분류 완료!"