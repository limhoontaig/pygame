# import requests
# from bs4 import BeautifulSoup
# def crawler(): 
    
#     url = 'https://www.google.com'
#     html = requests.get(url)
#     soup = BeautifulSoup(html, 'html.parser')
#     select = soup.head.find_all('meta')
#     for meta in select:
#         print(meta.get('content'))

# crawler()

# import urllib.request
# from bs4 import BeautifulSoup
 
# url = "news.naver.com"
# req = urllib.request.urlopen(url)
# res = req.read()
 
# soup = BeautifulSoup(res,'html.parser') # BeautifulSoup 객체생성
# keywords = soup.find_all('span',class_='ht_ico') # 데이터에서 태그와 클래스를 찾는 함수
# print(keywords)


import datetime
import urllib.request
from bs4 import BeautifulSoup
 
now = datetime.datetime.now()
nowDate = now.strftime('%Y년 %m월 %d일 %H시 %M분 입니다.')
print("\n       ※ Python Webcrawling Project 1 ※ \n ")
print('   환영합니다, ' + nowDate)
print('      오늘의 주요 정보를 요약해 드리겠습니다.\n')

# 오늘의 날씨
print('  ○>> #오늘의 #날씨 #요약 \n')
webpage = urllib.request.urlopen('https://search.naver.com/search.naver?where=nexearch&sm=top_sug.pre&fbm=1&acr=2&acq=dhsmfdml&qdt=0&ie=utf8&query=%EC%98%A4%EB%8A%98%EC%9D%98%EB%82%A0%EC%94%A8')
soup = BeautifulSoup(webpage, 'html.parser')
temps = soup.find('span',"todaytemp")
cast = soup.find('p',"cast_txt")
print('--> 서울 날씨 : ' , temps.get_text() , '℃' , cast.get_text())

webpage = urllib.request.urlopen('https://search.naver.com/search.naver?sm=top_hty&fbm=0&ie=utf8&query=%EB%8C%80%EA%B5%AC+%EB%82%A0%EC%94%A8')
soup = BeautifulSoup(webpage, 'html.parser')
temps = soup.find('span',"todaytemp")
cast = soup.find('p',"cast_txt")
print('--> 대구 날씨 : ' , temps.get_text() , '℃' , cast.get_text())

webpage = urllib.request.urlopen('https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&query=%EB%B6%80%EC%82%B0+%EB%82%A0%EC%94%A8&oquery=%EB%8C%80%EA%B5%AC+%EB%82%A0%EC%94%A8&tqi=UrZy%2Bsp0YidssAyki54ssssssKC-251380')
soup = BeautifulSoup(webpage, 'html.parser')
temps = soup.find('span',"todaytemp")
cast = soup.find('p',"cast_txt")
print('--> 부산 날씨 : ' , temps.get_text() , '℃' , cast.get_text())
print('\n')



# 오늘의 핫토픽
print('  ○>> #오늘의 #핫토픽 #헤드라인 \n')
webpage = urllib.request.urlopen('https://www.naver.com/')
soup = BeautifulSoup(webpage, 'html.parser')
for temps in soup.find_all('a',"issue"):
    print('--> ' , temps.get_text())
print('\n')


# 오늘의 코로나 현황
# https://h-glacier.tistory.com/

print('  ○>> #오늘의 #국내 #코로나19 #현황 \n')
webpage = urllib.request.urlopen('http://ncov.mohw.go.kr/')
soup = BeautifulSoup(webpage, 'html.parser')
dayconfirm = soup.find('span',"data")
allinfo = soup.find('span', 'num')
print(' --> 오늘의 신규 확진자 : ' , dayconfirm.get_text() , '\n --> 현재까지 확진자 : ', allinfo.get_text(),'\n\n')



# 오늘의 음원 TOP10
# https://h-glacier.tistory.com/

print('  ○>> #오늘의 #음원 #종합 #TOP10 \n')
webpage = urllib.request.urlopen('https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&query=%EC%9D%8C%EC%9B%90%EC%B0%A8%ED%8A%B8&oquery=%EB%A9%9C%EB%A1%A0%EC%B0%A8%ED%8A%B8&tqi=UrZ0HsprvN8ssK5ZP%2BsssssstVh-314088')
toptenlist = []
artistlist = []
Rank = 10
soup = BeautifulSoup(webpage, 'html.parser')
for topten in soup.find_all('div',"title"):
    toptenlist.append(topten.get_text())
# for artist in soup.find_all('a',"singer"):
#     artistlist.append(artist.get_text())

for i in range(len(toptenlist)):
    print(' - %2d위  : %s '%(i+1, toptenlist[i]))



from urllib.request import urlopen
from bs4 import BeautifulSoup
html = urlopen("http://www.naver.com")  
bsObject = BeautifulSoup(html, "html.parser") 
# print(bsObject) # 웹 문서 전체가 출력
print(bsObject.head.title) # <title>NAVER</title> 출력

for meta in bsObject.head.find_all('meta'):
    print(meta.get('content')) # 모든 메타 데이터의 내용 출력

# print (bsObject.head.find("meta", {"name":"description"})) # 원하는 태그의 내용 출력

for link in bsObject.find_all('a'):
    print(link.text.strip(), link.get('href')) #a 태그로 둘러싸인 텍스트와 a 태그의 href 속성을 출력




from urllib.request import urlopen
from bs4 import BeautifulSoup as bs

# 교보문고의 베스트셀러 웹페이지를 가져옵니다.

html = urlopen('http://www.kyobobook.co.kr/bestSellerNew/bestseller.laf')
bsObject = bs(html, "html.parser")

# 책의 상세 웹페이지 주소를 추출하여 리스트에 저장합니다.
book_page_urls = []
for cover in bsObject.find_all('div', {'class':'detail'}):
    link = cover.select('a')[0].get('href')
    book_page_urls.append(link)

# 메타 정보로부터 필요한 정보를 추출합니다.메타 정보에 없는 저자 정보만 따로 가져왔습니다.   
for index, book_page_url in enumerate(book_page_urls):
    html = urlopen(book_page_url)
    bsObject = bs(html, "html.parser")
    title = bsObject.find('meta', {'property':'rb:itemName'}).get('content')
    author = bsObject.select('span.name a')[0].text
    image = bsObject.find('meta', {'property':'rb:itemImage'}).get('content')
    url = bsObject.find('meta', {'property':'rb:itemUrl'}).get('content')
    originalPrice = bsObject.find('meta', {'property': 'rb:originalPrice'}).get('content')
    salePrice = bsObject.find('meta', {'property':'rb:salePrice'}).get('content')

    print(index+1, title, author, image, url, originalPrice, salePrice)

# soup = BeautifulSoup(res,'html.parser') # BeautifulSoup 객체생성
# keywords = soup.find_all('span',class_='ht_ico') # 데이터에서 태그와 클래스를 찾는 함수
# print(keywords)
