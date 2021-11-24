import os
import shutil
from tkinter import filedialog, font
import datetime

# 저장 경로 (폴더)
def browse_dest_path():
    folder_selected = filedialog.askdirectory()
    if folder_selected is None: # 사용자가 취소를 누를 때
      return
    #print(folder_selected)
    txt_dest_path.delete(0, END)
    txt_dest_path.insert(0, folder_selected)


folder_selected = filedialog.askdirectory()
# if folder_selected is None: # 사용자가 취소를 누를 때
  
for filename in os.listdir(folder_selected):
    info = os.stat(filename)
    print(info.st_mtime)


    # 만든시간을 타임 스탬프로 출력
    ctime = os.path.getctime(filename)
    # 수정시간을 타임 스탬프로 출력
    mtime = os.path.getmtime(filename)
    # 마지막 엑세스시간을 타임 스탬프로 출력
    atime = os.path.getatime(filename)
    # 파일크기
    filesize=os.path.getsize(filename)

    print(ctime, mtime, atime,filesize)

    #타임스탬프를 실제 시간으로 변경하기
    print (datetime.datetime.fromtimestamp(ctime))


# cwd = os.getcwd()
# # print(cwd)
# rootpath = folder_selected
# if not os.path.isdir(rootpath):
#   os.mkdir(rootpath)

# # for (path, dir, files) in os.walk(rootpath):
# #     for filename in files:
# #         ext = os.path.splitext(filename)[-1]
# #         if ext == '.jpg' or '.jpeg':
# #             print("%s/%s" % (path, filename))





# # walk = os.walk(rootpath)
# # for path, direct, files in walk:
# #   print(path, direct, files)
# #   total_files = []
# #   total_files.append.files
# # print(total_files)

# # print(walk)
# files = os.listdir(rootpath)
# # print(files)
# for file in files:
#   new_dir = file.split('_')[0]
#   print(new_dir)
#   try:
#     os.mkdir(rootpath+'\\'+new_dir)
#   except FileExistsError as e:
#     print(e)
#   source = os.path.join(rootpath,file)
#   destination = os.path.join(rootpath,new_dir,file)
  
#   if os.path.isdir(source):
#     pass
#   else:
#     shutil.move(source, destination)
  
# print('end')
