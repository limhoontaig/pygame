'''
l = [i if i % 2 == 0 else None for i in range(5) ]
print(l)

l = [i for i in range(5) if i % 2 == 0]
print(l)

a = map(lambda x : x * 2 , [1,2,3,4])
b = lambda x : x * 2 , [1,2,3,4]
print(b)
print(list(b))
print(a)
print(list(a))

a = 100
def func():
  global a
  a = a + 20
  return a

c = func()
print('func() = ', c)
print('a =', a)


class BusinessCard:
  def __init__(self, name, email, addr):
      self.name = name
      self.email = email
      self.addr = addr
  def print_info(self):
      print("--------------------")
      print("Name: ", self.name)
      print("E-mail: ", self.email)
      print("Address: ", self.addr)
      print("--------------------")

member1 = BusinessCard("Kangsan Lee", "kangsan.lee@korea.co.kr", "USA")
member1.print_info()

class Foo:
  def func1():
    print("function 1")

  def func2(self):
    print(id(self))
    print("function 2")

f = Foo()
f2 = Foo()
print('id f : ', id(f))
f.func1()
print('id f2 : ', id(f2))
f.func2()
f2.func2()


class Stock:
    market = "kospi"

print(dir())

Stock1 = Stock()
print(Stock)
print('id Stock : ', id(Stock))
print(Stock1)
print(list[Stock1])
print('id Stock1 :', id(Stock1))
print(Stock.__dict__)



class Account:
  num_accounts = 0
  def __init__(self, name):
    self.name = name
    Account.num_accounts += 1
  def __del__(self):
    Account.num_accounts -= 1

kim = Account("kim")
kim.num_accounts = 1
lee = Account("lee")
print('class Account __dict__ :', Account.__dict__)
print('kim.num_accounts :', kim.num_accounts)
print('print(kim.__dict__) ', kim.__dict__)
print('lee.num_accounts : ', lee.num_accounts)
print('lee.__dict__ : ', lee.__dict__)

'''
import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf
yf.pdr_override()

# 종목 타입에 따라 download url이 다름. 종목코드 뒤에 .KS .KQ등이 입력되어야해서 Download Link 구분 필요
stock_type = {
    'kospi': 'stockMkt',
    'kosdaq': 'kosdaqMkt'
}

# 회사명으로 주식 종목 코드를 획득할 수 있도록 하는 함수
def get_code(df, name):
  code = df.query("name=='{}'".format(name))['code'].to_string(index=False)
  
  # 위와같이 code명을 가져오면 앞에 공백이 붙어있는 상황이 발생하여 앞뒤로 sript() 하여 공백 제거
  code = code.strip()
  return code

# download url 조합
def get_download_stock(market_type=None):
  market_type_param = stock_type[market_type]
  download_link = 'http://kind.krx.co.kr/corpgeneral/corpList.do'
  download_link = download_link + '?method=download'
  download_link = download_link + '&marketType=' + market_type_param

  df = pd.read_html(download_link, header=0)[0]
  return df;

# kospi 종목코드 목록 다운로드
def get_download_kospi():
  df = get_download_stock('kospi')
  df.종목코드 = df.종목코드.map('{:06d}.KS'.format)
  return df

# kosdaq 종목코드 목록 다운로드
def get_download_kosdaq():
  df = get_download_stock('kosdaq')
  df.종목코드 = df.종목코드.map('{:06d}.KQ'.format)
  return df

# kospi, kosdaq 종목코드 각각 다운로드
kospi_df = get_download_kospi()
kosdaq_df = get_download_kosdaq()

# data frame merge
code_df = pd.concat([kospi_df, kosdaq_df])

# data frame정리
code_df = code_df[['회사명', '종목코드']]

# data frame title 변경 '회사명' = name, 종목코드 = 'code'
code_df = code_df.rename(columns={'회사명': 'name', '종목코드': 'code'})

print(code_df)  

import matplotlib.pyplot as plt

code = get_code(code_df, '삼성전자')

df = pdr.get_data_yahoo(code)

df['Close'].plot()

# 수정주가를 반영
df = pdr.get_data_yahoo(code, adjust_price=True)

print(df['Close'].plot(figsize=(10, 5)))

