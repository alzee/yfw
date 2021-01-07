#!/usr/bin/python3
# 抓取 https://www.yaofangwang.com/yaodian/379739/medicines.html 页面所有单品

# 导入模块
import requests
from bs4 import BeautifulSoup
import pymysql.cursors
import redis
from progress.bar import Bar

# 创建 mysql 对象
conn = pymysql.connect(
        host='localhost',
        user='yfw',
        password='yfw',
        db='yfw',
        cursorclass=pymysql.cursors.DictCursor
        )
cursor = conn.cursor()

# 创建 redis 对象
redis = redis.Redis(host='localhost', decode_responses=True)

sql = "select drugId from drug"
cursor.execute(sql)
res = cursor.fetchall()
alreadyHave = []
for i in res:
    alreadyHave.append(i['drugId'])

def main():
    global drugs
    drugs = redis.hgetall('drug')
    if (len(drugs) == 0):
        url = 'https://www.yaofangwang.com/yaodian/379739/medicines.html'
        soup = getSoup(url)
        count = soup.select_one('.tabnav .count b').string.strip()
        pageCount = soup.select_one('span.num').text.strip().lstrip('1 ').lstrip('/ ')
        bar = Bar('正在获取商品编号...', max=int(count))
        for i in range(1, int(pageCount) + 1):
            url = f'https://www.yaofangwang.com/yaodian/379739/medicines.html?page={i}'
            soup = getSoup(url)
            li = soup.select('ul.goods3 li')
            for i in li:
                url = 'https:' + i.a['href']
                # print(url)
                soup = getSoup(url)
                drugId = soup.select_one('#aFavorite')['data-mid']
                ourPrice = soup.select_one('#pricedl .money .num').string.strip()
                redis.hset('drug', drugId, ourPrice)
                bar.next()
        bar.finish()
        drugs = redis.hgetall('drug')

    bar = Bar('正在抓取商品信息...', max=len(drugs))
    for i in drugs:
        # getPrice(i)
        getInfo(i)
        bar.next()
    bar.finish()


def getSoup(url):
    """ 返回 BeautifulSoup 对象 """
    headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'}
    html = requests.get(url, headers=headers).text
    return BeautifulSoup(html, 'html.parser')

def getInfo(drugId):
    url = 'https://www.yaofangwang.com/medicine-' + str(drugId) + '.html?sort=sprice&sorttype=desc'
    # print(url)
    soup = getSoup(url)
    
    retailerCount = soup.select_one('#priceABtn b').string
    
    if int(retailerCount) == 0:
        exit()
    
    priceMin = soup.select_one('.maininfo div.info label.num').text.rstrip(' 起')

    priceMaxTag = soup.select_one('#slist .slist li p.money')
    if priceMaxTag == None:
        priceMax = ''
    else:
        priceMax = priceMaxTag.string.strip().lstrip('¥')


    if int(drugId) in alreadyHave:
        #print('Updating', drugId, '...')
        sql = f"update drug set ourPrice = '{drugs[drugId]}', priceMax = '{priceMax}', priceMin = '{priceMin}' where drugId = '{drugId}'"
    else:
        info = soup.select('div.maininfo div.info dd')
        name = info[0].string
        if info[2].div == None:
            spec = info[2].text.strip()
        else:
            spec = info[2].div.div.text.strip()
        form = info[3].string
        manufacturer = info[4].string
        # print(name, spec, form, manufacturer)
        imgURL = 'https:' + soup.select_one('div.maininfo div.info dd img')['src']
        #print('Inserting', drugId, '...')
        sql = f"insert into drug (drugId, name, spec, form, manufacturer, ourPrice, priceMax, priceMin, imgURL) values ('{drugId}', '{name}', '{spec}', '{form}', '{manufacturer}', '{drugs[drugId]}', '{priceMax}', '{priceMin}', '{imgURL}')"
    try:
        #print(sql)
        cursor.execute(sql)
        redis.hdel('drug', drugId)
        # print(cursor.fetchall())
    except:
        print('We already have', drugId)
    conn.commit()


def getPrice(drugId):
    url = 'https://www.yaofangwang.com/medicine-' + str(drugId) + '.html'
    soup = getSoup(url)
    pagenum = soup.select_one('#slist span.num').text.strip().lstrip('1 ').lstrip('/ ')
    for i in range(2, int(pagenum) + 1):
        url = 'https://www.yaofangwang.com/medicine-' + str(drugId) + '-p' + str(i) + '.html'
        soup = getSoup(url)
        li = soup.select('#slist .slist li')
        for i in li:
            price = i.select_one('p.money').string.strip().lstrip('¥')
            retailer = i.select_one('a.stitle').string
            # print(price, retailer)
            sql = f"insert into price (drugId, price, retailer) values ('{drugId}', '{price}', '{retailer}')"
            cursor.execute(sql)
            # print(cursor.fetchall())
            conn.commit()

main()
