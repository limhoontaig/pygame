#!/usr/bin/env python
# coding: utf-8

# # 필요 Module import

# In[1]:


import pandas as pd
import os
import numpy as np
import tkinter
from tkinter import filedialog
from datetime import datetime


# # 종합 할인금액 입력

# In[2]:


def fileselection(file_title):
    root = tkinter.Tk()
    root.withdraw()
    file_title= file_title
    #dir_path = os.getcwd()
    dir_path = 'D:/과장/1 부과자료/2021년'
    # dir_path = filedialog.askdirectory(parent=root,initialdir="/",title='Please select a directory')
    file_path = filedialog.askopenfilename(parent=root,initialdir=dir_path,
                                           title = file_title)
    return file_path


# # 수도 다자녀 할인 파일 열기

# In[3]:


file_path = fileselection('Please select a file of 수도 다자녀할인')


# In[4]:


df = pd.read_excel(file_path,sheet_name=0, skiprows=0)

#df['동'] = df['동호수(복지개별)'].parse('-', 0)
# new list of data frame with split value columns
new = df['동호수(복지개별)'].str.split("-", n = 1, expand = True)
  
# making separate first name column from new data frame
df["동"]= new[0]
  
# making separate last name column from new data frame
df["호"]= new[1]
  
# Dropping old Name columns
df.drop(columns =["No","동호수(복지개별)"], inplace = True)

# making 복지코드 on '복지코드' column from XPERP Code
df["복지코드"]= '3'
  
# df display
# df.head()


# In[5]:


### XPERP Code 유공자: 2, 기초생활:3, 다자녀:I(Capital i), 중복할인: V(Capital v)  ###

# 다자녀 시트 읽어오기
df_f = pd.read_excel(file_path, sheet_name=1,skiprows=0)

# new data frame with split value columns
new = df_f['동호수(다자녀감면)'].str.split("-", n = 1, expand = True)
  
# making separate 동 name column from new data frame
df_f["동"]= new[0]
  
# making separate 호 name column from new data frame
df_f["호"]= new[1]

# making 복지코드 on '복지코드' column from XPERP Code
df_f["복지코드"]= 'I' # Capital I
  
# Dropping old Name columns
df_f.drop(columns =["No","동호수(다자녀감면)"], inplace = True)
  
# df_f.head()


# # 수도 유공자할인 등록 

# In[6]:


file_path = fileselection('Please select a file of 수도 유공자할인')


# In[7]:


df_3 = pd.read_excel(file_path, sheet_name=0, skiprows=5)
# new data frame with split value columns
new = df_3['동호수'].str.split("-", n = 1, expand = True)
# making separate first name column from new data frame
df_3["동"]= new[0]
# making separate last name column from new data frame
df_3["호"]= new[1]
# Dropping old Name columns
df_3.drop(columns =["No","고객번호","수전주소","동호수"], inplace = True)
# making 복지코드 on '복지코드' column from XPERP Code
df_3["복지코드"]= '2'


# In[8]:


dis = pd.merge(df, df_f, how = 'outer', on = ['동','호'])
dis1 = pd.merge(dis, df_3, how = 'outer', on = ['동','호'])


# In[9]:


#discount_1.fillna(0)
con1 = (dis1.복지코드_x=='3')
con2 = (dis1.복지코드_y=='I')
con3 = (dis1.복지코드=='2')
dis1.loc[con1, 'Code'] = '3'
dis1.loc[con2, 'Code'] = 'I'
dis1.loc[con3, 'Code'] = '2'
dis1.loc[(con1 & con2)|(con1&con3)|(con2&con3)|(con1&con2&con3), 'Code'] = 'V'
dis2 = dis1[['동','호','Code']]


# In[10]:


dis2['동'] = pd.to_numeric(dis2['동'])
dis2['호'] = pd.to_numeric(dis2['호'])


# # 복지종류별 입력하기

# # Template dataframe 작성
# 

# In[11]:


file_path = fileselection('Please open a Template File')
df_x = pd.read_excel(file_path,skiprows=0)


# In[12]:


# discount df 생성 (Template df(df_x)에 감면코드(discount) merge
discount = pd.merge(df_x, dis2, how = 'outer', on = ['동','호'])
# 감면구분 코드를 Code Data로 Update
discount['감면구분'] = discount['Code']
# Code 임시데이터 columns를 drop
discount = discount.drop(['Code'],axis=1)


# # File save location selection and data 생성

# In[13]:


root = tkinter.Tk()
root.withdraw()
file_title= "Please select a directory to save a file"
dir_path = 'D:\\과장\\1 1 부과자료\\2021년'
dir_path = filedialog.askdirectory(parent=root,initialdir=dir_path,title=file_title)


# In[14]:


#작업월을 파일이름에 넣기 위한 코드 (작업일 기준)
now = datetime.now()
dt1 = now.strftime("%Y")+now.strftime("%m")
dt1 = dt1+'XPERP_Water_Upload.xls'
#file save
discount.to_excel(dir_path + '/' + dt1,index=False,header=False)


# In[ ]:




