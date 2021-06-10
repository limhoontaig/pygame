#!/usr/bin/env python
# coding: utf-8

# # 필요한 Module Import

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
    dir_path = 'D:/과장/1 부과자료/2021년'
    file_path = filedialog.askopenfilename(parent=root,initialdir=dir_path,
                                           title = file_title)
    return file_path


# In[5]:


file_path = fileselection('Please select a file of 한전 종합복지할인액')




df = pd.read_excel(file_path,skiprows=2)#, dtype={'동':int, '호':int}) #,thousands=',')


# In[9]:


df


# In[7]:


df1 = df.dropna(subset=['동'])
# Template Columns중에서 필수 Columns만 복사하여 DataFrame 생성용 Columns list 생성
df2col =['동','호', '필수사용\n공제', '할인\n구분','복지할인']
# df2 DataFrame columns중에서 dtype float를 int로 바꿀 Columns list 생성
df2col_f =['동','호', '필수사용\n공제', '복지할인']


# In[8]:


# SettingWithCopyWarning Error 방지를 위하여 copy() method적용
df2 = df1[df2col].copy()
df2[df2col_f] = df2[df2col_f].astype('int')


# # 복지종류별 입력하기

# In[10]:


file_path = fileselection('Please select a file of 한전 세대별 복지할인 종류 및 금액')
df_w = pd.read_excel(file_path,skiprows=2, thousands=',')#, dtype={'동':int, '호':int}) #,thousands=',')
df_w = df_w[['동','호','복지구분','할인요금']]


# In[11]:


# 복지구분 컬럼을 선택합니다.
# 컬럼의 값에 대가족할인 항목을 또는(|) 대가족할인 항목늬 문자열이 포함되어있는지 판단합니다.
# 그 결과를 새로운 변수에 할당합니다.
contains_family = df_w['복지구분'].str.contains('다자녀할인|대가족할인|출산가구할인')

# 대가족할인 조건를 충족하는 데이터를 필터링하여 새로운 변수에 저장합니다.
subset_df_f = df_w[contains_family].copy()
subset_df_f.set_index(['동','호'],inplace=True)
#subset_df_f['복지코드'] = subset_df_f['복지구분']
subset_df_f.loc[subset_df_f.복지구분 == '다자녀할인', '복지코드'] = '3'
subset_df_f.loc[subset_df_f.복지구분 == '대가족할인', '복지코드'] = '1'
subset_df_f.loc[subset_df_f.복지구분 == '출산가구할인', '복지코드'] = '2'

# 복지할인 조건를 충족(대가족할인이 아닌것 ~)하는 데이터를 필터링하여 새로운 변수에 저장합니다.
subset_df_w = df_w[~contains_family].copy()
subset_df_w.set_index(['동','호'],inplace=True)
subset_df_w.loc[subset_df_w.복지구분 == '기초생활할인', '복지코드'] = 'G'
subset_df_w.loc[subset_df_w.복지구분 == '독립유공자할인', '복지코드'] = 'A'
subset_df_w.loc[subset_df_w.복지구분 == '사회복지할인', '복지코드'] = 'G'
subset_df_w.loc[subset_df_w.복지구분 == '의료기기할인', '복지코드'] = 'G'
subset_df_w.loc[subset_df_w.복지구분 == '장애인할인', '복지코드'] = 'D'
subset_df_w.loc[subset_df_w.복지구분 == '차상위할인', '복지코드'] = 'I'


# # Open Template file for XPERP upload and data 작성

# In[12]:


file_path = fileselection('Please open a Template File')
df_x = pd.read_excel(file_path,skiprows=0)
# xperp upload template 양식의 columns list 생성
df_x_cl = df_x.columns.tolist()
# 동호를 indexing하여 dataFrame merge 준비
df_x.set_index(['동','호'],inplace=True)


# In[13]:


# discount df 생성 (Template df(df_x)에 필수사용공제(df2) merge
discount = pd.merge(df_x, df2, how = 'outer', on = ['동','호'])
# 사용량 보장공제를 한전금액(필수사용\n공제) Data로 Update
discount['사용량보장공제'] = discount['필수사용\n공제']
# 사용량 보장공제 임시데이터 columns를 drop
discount = discount.drop(['필수사용\n공제','할인\n구분','복지할인'],axis=1)


# In[14]:


# Template df에 필수사용공제 merge
discount = pd.merge(discount, subset_df_f, how = 'outer', on = ['동','호'])
discount['대가족할인액'] = discount['할인요금']
discount['대가족할인구분'] = discount['복지코드']
discount = discount.drop(['복지코드','할인요금','복지구분'],axis=1)


# In[15]:


discount = pd.merge(discount, subset_df_w, how = 'outer', on = ['동','호'])
#discount1 = discount.reset_index()
discount['복지할인액'] = discount['할인요금']
discount['복지할인구분'] = discount['복지코드']
discount = discount.drop(['복지코드','할인요금','복지구분'],axis=1)
#discount.to_excel('복지할인.xlsx')
#discount.head(1)


# # Final Data Save location selection and Save

# In[16]:


root = tkinter.Tk()
root.withdraw()
file_title= "Please select a directory to save a file"
#dir_path = os.getcwd()
dir_path = 'D:\\과장\\1 1 부과자료\\2021년'
cwd = os.getcwd()
dir_path = filedialog.askdirectory(parent=root,initialdir=dir_path,title=file_title)


# In[17]:


#작업월을 파일이름에 넣기 위한 코드 (작업일 기준)
now = datetime.now()
dt1 = now.strftime("%Y")+now.strftime("%m")
dt1 = dt1+'ELEC_XPERP_Upload.xls'
#file save
discount.to_excel(dir_path + '/' + dt1,index=False,header=False)


# In[ ]:




