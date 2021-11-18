import os
import shutil

cwd = os.getcwd()
print(cwd)
rootpath = cwd+'\\pictures'
files = os.listdir(rootpath)
print(files)
for file in files:
  new_dir = file.split('_')[0]
  print(new_dir)
  try:
    os.mkdir(rootpath+'\\'+new_dir)
  except FileExistsError as e:
    print(e)
  source = rootpath+'\\'+file
  destination = rootpath+'\\'+new_dir+'\\'+file
  
  shutil.move(source, destination)
print('end')
