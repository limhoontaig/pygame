import csv
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from urllib.parse import quote_plus


baseUrl = 'https://www.google.co.kr/search?q='
plusUrl = input('검색어를 입력하세요 : ')
# 한글 검색 자동 변환
url = baseUrl + quote_plus(plusUrl)

driver = webdriver.Chrome()
driver.get(url)


html = driver.page_source
soup = bs(html, "html.parser")

r = soup.select('.r')
searchList = []

for i in r:
    temp = []
    temp.append(i.select_one('.LC20lb').text) # 제목
    temp.append(i.a.attrs['href']) # 링크
    print()
    searchList.append(temp)

driver.close()

f = open(f'{plusUrl}.csv', 'w', encoding = 'cp949', newline='')
csvWriter = csv.writer(f)
for i in searchList:
    # 한줄씩 써 내려감
    csvWriter.writerow(i)
f.close()

print('완료 되었습니다.')