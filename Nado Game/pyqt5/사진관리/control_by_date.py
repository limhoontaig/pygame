# -*- coding: utf-8 -*-
"""
1. 파일 경로를 잡는다.
2. 해당 경로 내 모든 사진파일 확장자를 가진 파일을 읽는다.
3. 해당 파일들의 속성에서 일자를 가져온다.
4. 가져온 일자들의 유니크 값을 생성해서, 해당 값들로 폴더를 생성한다.
5. 생성한 폴더에 각 일자의 사진들을 옮긴다.
6. 옮길 때, 동일한 파일이 있을 경우 continue
"""
"""
    함수화는 나중에 일단 구현
"""
import os
import shutil
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

target_folder = 'E:\\source\\pygame\\Nado Game\\pyqt5\\사진관리\\data\\'
img_folder = 'E:\\source\\pygame\\Nado Game\\pyqt5\\사진관리\\img_result\\'
video_folder = 'E:\\source\\pygame\\Nado Game\\pyqt5\\사진관리\\video_result\\'

folder_list = os.listdir(target_folder)

# set(map(lambda x: x.split('.')[1],file_list))
# 가지고 와야하는 이미지 파일이 JPG만 있음
# 영상은 MOV,MP4

def split_files(file_folder,file_list,type_folder,target_type):
    file_dict = {}
    for f in file_list:
        if target_type == 'image':
            image = Image.open(file_folder+f)
            exifdata = image.getexif()
            
            for tag_id in exifdata:
                tag = TAGS.get(tag_id,tag_id)
                data = exifdata.get(tag_id)
                if tag  == 'DateTime':  
                    break
            if tag == 'DateTime':
                file_date = datetime.strptime(data.split(" ")[0],"%Y:%m:%d")
            else:            
                file_stat = os.stat(file_folder+f)
                file_date = datetime.fromtimestamp(file_stat.st_mtime)
        else:
            file_stat = os.stat(file_folder+f)
            file_date = datetime.fromtimestamp(file_stat.st_mtime)
        month = file_date.month
        day = file_date.day
        date = ''
        if month < 10:
            if day < 10:
                date = '0'+str(month) +'0'+ str(day)
            else:
                date = '0'+str(month) + str(day)
        else:
            if day < 10:
                date = str(month) +'0'+ str(day)
            else:
                date = str(month) + str(day)
        file_dict[f] = date
    
    for mkfolder in set(list(file_dict.values())):
        if not os.path.isdir(type_folder+mkfolder):
            os.mkdir(type_folder+mkfolder)
            
    for file_name, file_date in file_dict.items():
        if os.path.isfile(os.path.join(type_folder,file_date,file_name)):
            # new_file_name = file_name.split('.')[0]+str(datetime.now().microsecond)+'.'+file_name.split('.')[1]
            # os.rename(file_folder+file_name,file_folder+new_file_name)
            # shutil.copy2(file_folder+new_file_name, type_folder+file_date)
            continue
        else:
            shutil.copy2(file_folder+file_name, type_folder+file_date)
    
for folder in folder_list:
    img_list = []
    video_list = []
    file_folder = target_folder+folder+'\\'
    file_list = os.listdir(file_folder)
    for f in file_list:
        if f.split('.')[1] == 'JPG' or f.split('.')[1] == 'jpg':
            img_list.append(f)
        elif f.split('.')[1] == 'MOV' or f.split('.')[1] == 'MP4':
            video_list.append(f)
    split_files(file_folder,img_list,img_folder,'image')
    split_files(file_folder,video_list,video_folder,'video')