import os
import shutil

cwd = os.getcwd()
# print(cwd)
rootpath = cwd+'\\pictures'
if not os.path.isdir(rootpath):
  os.mkdir(rootpath)

for (path, dir, files) in os.walk(rootpath):
    for filename in files:
        ext = os.path.splitext(filename)[-1]
        if ext == '.jpg'|'.jpeg':
            print("%s/%s" % (path, filename))





walk = os.walk(rootpath)
for path, direct, files in walk:
  print(path, direct, files)
#   total_files = []
#   total_files.append.files
# print(total_files)

# print(walk)
# files = os.listdir(rootpath)
# print(files)
for file in files:
  new_dir = file.split('_')[0]
  print(new_dir)
  try:
    os.mkdir(rootpath+'\\'+new_dir)
  except FileExistsError as e:
    print(e)
  source = os.path.join(rootpath,file)
  destination = os.path.join(rootpath,new_dir,file)
  
  if os.path.isdir(source):
    pass
  else:
    shutil.move(source, destination)
  
print('end')
