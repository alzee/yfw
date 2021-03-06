#!/usr/bin/python3
# 抓取 https://www.yaofangwang.com/yaodian/379739/medicines.html 页面所有单品

# 导入模块
import requests
import time
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
redisHash = 'drug'

def main():
    global drugs
    drugs = redis.hgetall(redisHash)
    if len(drugs) == 0:
        url = 'https://www.yaofangwang.com/yaodian/379739/medicines.html'
        soup = getSoup(url)
        count = soup.select_one('.tabnav .count b').string.strip()

        bar = Bar('正在获取商品编号...', max=int(count))
        while True:
            li = soup.select('ul.goods3 li')
            for i in li:
                detailUrl = 'https:' + i.a['href'] # https://www.yaofangwang.com/detail-xxxxxxxx.html
                detailSoup = getSoup(detailUrl)
                try:
                    approvalNum = detailSoup.select_one('head title').text.split(',')[-1].split('_')[0]
                    ourPrice = detailSoup.select_one('#pricedl .money .num').string.strip()
                    drugId = detailSoup.select_one('#aFavorite')['data-mid']
                    ourStock = detailSoup.select_one('#reserve').string.strip()
                except AttributeError:
                    pass
                except IndexError:
                    pass
                else:
                    redis.hset(redisHash, drugId, ourPrice + ':' + approvalNum + ':' + ourStock)
                bar.next()
            nextPage = soup.select_one('div.pager div.list a.next')
            if nextPage == None:
                break
            url = 'https://www.yaofangwang.com' + nextPage['href']
            soup = getSoup(url)
        bar.finish()
        drugs = redis.hgetall(redisHash)

    bar = Bar('正在抓取商品信息...', max=len(drugs))
    for i in drugs:
        # getPrice(i)
        getInfo(i)
        bar.next()
    bar.finish()
    redis.delete(redisHash)

def getSoup(url):
    """ 返回 BeautifulSoup 对象 """
    headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'}
    html = requests.get(url, headers=headers).text
    return BeautifulSoup(html, 'html.parser')

def getInfo(drugId):
    # get priceMin
    url = 'https://www.yaofangwang.com/medicine-' + str(drugId) + '.html?sort=sprice&sorttype=asc'
    soup = getSoup(url)

    retailerCount = soup.select_one('#priceABtn b')
    if retailerCount != None:
        retailerCount = int(retailerCount.string)
        if retailerCount == 0:
            return
    else:
        return

    priceList = soup.select('#slist .slist li')
    priceMin = priceList[0].select_one('p.money').string.strip().lstrip('¥')
    stockPriceMin = priceList[0].select_one('.info .sreserve').string.strip()
    if retailerCount > 1:
        priceMin2 = priceList[1].select_one('p.money').string.strip().lstrip('¥')
        stockPriceMin2 = priceList[1].select_one('.info .sreserve').string.strip()
    else:
        priceMin2 = ''
        stockPriceMin2 = ''

    # get priceMax
    #url = 'https://www.yaofangwang.com/medicine-' + str(drugId) + '.html?sort=sprice&sorttype=desc'
    #soup = getSoup(url)

    #priceTag = soup.select_one('#slist .slist li p.money')
    #if priceTag == None:
    #    priceMax = ''
    #else:
    #    priceMax = priceTag.string.strip().lstrip('¥')
    priceMax = ''

    ourPrice = drugs[drugId].split(':')[0]
    approvalNum = drugs[drugId].split(':')[1]
    ourStock = drugs[drugId].split(':')[2]
    info = soup.select('div.maininfo div.info dd')
    name = info[0].string
    if info[2].div == None:
        spec = info[2].text.strip()
    else:
        spec = info[2].div.div.text.strip()
    form = info[3].string
    manufacturer = info[4].string
    #imgURL = 'https:' + soup.select_one('div.maininfo div.info dd img')['src']
    imgURL = ''

    sql = "select drugId from drug"
    cursor.execute(sql)
    res = cursor.fetchall()
    alreadyHave = []
    for i in res:
        alreadyHave.append(i['drugId'])

    if int(drugId) in alreadyHave:
        #print('Updating', drugId, '...')
        sql = f"update drug set approvalNum = '{approvalNum}', name = '{name}', spec = '{spec}', form = '{form}', manufacturer = '{manufacturer}', ourPrice = '{ourPrice}', ourStock = '{ourStock}', priceMax = '{priceMax}', priceMin = '{priceMin}', stockPriceMin = '{stockPriceMin}', priceMin2 = '{priceMin2}', stockPriceMin2 = '{stockPriceMin2}', imgURL = '{imgURL}', updateOn = CURRENT_TIMESTAMP where drugId = '{drugId}'"
    else:
        #print('Inserting', drugId, '...')
        sql = f"insert into drug (drugId, approvalNum, name, spec, form, manufacturer, ourPrice, ourStock, priceMax, priceMin, stockPriceMin, priceMin2, stockPriceMin2, imgURL) values ('{drugId}', '{approvalNum}', '{name}', '{spec}', '{form}', '{manufacturer}', '{ourPrice}', '{ourStock}', '{priceMax}', '{priceMin}', '{stockPriceMin}', '{priceMin2}', '{stockPriceMin2}', '{imgURL}')"
    try:
        cursor.execute(sql)
        redis.hdel(redisHash, drugId)
        # print(cursor.fetchall())
    except:
        print('error when processing drugId:', drugId)
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
