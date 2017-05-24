#!/usr/bin/python
# -*- coding: UTF-8 -*-

import requests
from bs4 import BeautifulSoup
import threading
import pymysql
import configparser
import sys
import re
import traceback
import  datetime
from db_connection import  db_connection


class GetHouseInfoFromFang(threading.Thread):
    CHARSET_DEFALUT = 'gb2312'
    PAGE_NUM = 20
    db = ''
    dbCursor =''
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Upgrade-Insecure-Requests": "1",
        "Content-Type": "application/x-www-form-urlencoded; charset=gb2312",
        "Pragma": "no-cache",
        "Accept-Encoding": "gzip, deflate, br",
        'Connection': 'close'
    }

    def __init__(self, houseInfoUrl):
        print("抓取房天下数据初始化")
        threading.Thread.__init__(self)
        requests.adapters.DEFAULT_RETRIES = 5
        requests.session().keep_alive = False

        self.houseInfoUrl = houseInfoUrl
        self.db = db_connection.get_db()
        self.dbCursor = self.db.cursor()
        # 获取配置文件
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")



    def getHouseListInfo(self):
        index_page = requests.get(self.houseInfoUrl, headers=GetHouseInfoFromFang.headers, timeout=120)
        pattern = re.compile(r"^http://", re.IGNORECASE)
        BS = BeautifulSoup(index_page.content.decode(GetHouseInfoFromFang.CHARSET_DEFALUT, 'ignore'), "html.parser")
        pageNavgUrlList  = BS.find('div', class_="page").find('li',attrs={'class': 'fr'}).find_all('a')
        endFix = self.houseInfoUrl.index('.com')
        hostUrl = self.houseInfoUrl[0:endFix] + '.com'
        urlList = []
        urlList.append(self.houseInfoUrl)
        flag = 0
        for pageNav in pageNavgUrlList:
            flag = flag + 1
            if flag == 1:
                continue
            pageUrl =  pageNav['href']
            pageValue = pageNav.get_text()
            if pageValue !='首页' and pageValue !='下一页'  and pageValue !='尾页':
                if not pattern.match(pageUrl):
                    urlList.append(hostUrl + pageUrl)
                else:
                    urlList.append(pageUrl)
        for url in urlList:
            list_page = requests.get(url, headers=GetHouseInfoFromFang.headers, timeout=120)
            ListBS = BeautifulSoup(list_page.content.decode(GetHouseInfoFromFang.CHARSET_DEFALUT, 'ignore'), "html.parser")
            houseDiv = ListBS.find('div', class_="nhouse_list").find('ul').find_all('li')
            for index in houseDiv:
                try:
                    houseName = index.find('div', attrs={'class': 'nlcd_name'}).find('a').get_text().strip()
                    houseAddress = index.find('div', attrs={'class': 'address'}).find('a').get_text().strip()
                    begin = houseAddress.index('[') + 1
                    end = houseAddress.index(']')
                    houseArea = houseAddress[begin:end] + '区'
                    # 查询地区ID
                    queryAreaSql = 'SELECT * FROM T_AREA t WHERE t.AREA_NAME=%s'
                    self.dbCursor.execute(queryAreaSql, (houseArea))
                    result = self.dbCursor.fetchone()
                    areaId = result[0]
                    houseDetailUrl = index.find('div', attrs={'class': 'nlcd_name'}).find('a')['href']
                    if pattern.match(houseDetailUrl):
                        print('houseDetailUrl:',houseDetailUrl)
                        detail_page = requests.get(houseDetailUrl, headers=GetHouseInfoFromFang.headers, timeout=60)
                        detailBS = BeautifulSoup(
                            detail_page.content.decode(GetHouseInfoFromFang.CHARSET_DEFALUT, 'ignore'),
                            "html.parser")
                        detailInfo = detailBS.find('div', attrs={'class': 'information'})
                        detailHouseName = detailInfo.find('div', attrs={'class': 'tit'}).find(
                            'strong').get_text().strip()
                        detailHouseAliasName = detailInfo.find('div', attrs={'class': 'tit'}).find(
                            'span').get_text().strip()
                        if detailHouseAliasName == '／5分' or detailHouseAliasName == '':
                            detailHouseAliasName = detailHouseName
                        else:
                            detailHouseAliasName = detailHouseAliasName.replace('别名：', '')
                        price = detailInfo.find('span', attrs={'class': 'prib cn_ff'}).get_text().strip()
                        if price == '待定':
                            price = '0'
                        houseTagList = detailInfo.find('div', attrs={'class': 'biaoqian1'}).find_all('a')
                        addressHtml = detailInfo.find('div', attrs={'id': 'xfptxq_B04_12'})
                        if addressHtml is None:
                            addressHtml = detailInfo.find('div', attrs={'id': 'xfdsxq_B04_12'})
                        detailHouseAddress = addressHtml.find('span').get_text().strip()
                        saleInfoHtml = detailInfo.find('a', attrs={'id': 'xfptxq_B04_23'})
                        if saleInfoHtml is None:
                            saleInfoHtml = detailInfo.find('a', attrs={'id': 'xfdsxq_B04_23'})
                        saleInfo = saleInfoHtml.get_text().strip()
                        saleTel = detailBS.find('span', attrs={'id': 'shadow_tel'}).get_text().strip()
                        tagName = ''
                        for tag in houseTagList:
                            tagName = tagName + tag.get_text() + ','
                        mainRoomList = detailInfo.find('div', attrs={'class': 'fl zlhx'}).find_all('a')
                        for mainRoom in mainRoomList:
                            mainRoomName = mainRoom.get_text()
                            if mainRoomName != '':
                                pass

                        # navUrlList = detailBS.find('div', attrs={'id': 'orginalNaviBox'}).find_all('a')
                        # for navIndex in navUrlList:
                        #     navHref = navIndex['href']
                        #     navText = navIndex.get_text()
                        #     if '楼盘详情' == navText:
                        #         pass
                        sysDate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        # 如果数据库存在楼盘新，更新楼盘信息
                        qryHouseInfoSql = 'SELECT * FROM T_HOUSE_INFO t WHERE t.HOUSE_NAME=%s'
                        self.dbCursor.execute(qryHouseInfoSql, (detailHouseName))
                        result = self.dbCursor.fetchone()
                        if result is None:
                            replace_data = \
                                (sysDate, sysDate, detailHouseName, detailHouseAliasName, price, areaId,
                                 detailHouseAddress,saleInfo, saleTel, '1', tagName, '', '')
                            self.addHouseInfo(replace_data)
                            self.dbCursor.execute(qryHouseInfoSql, (detailHouseName))
                            dbResult  = self.dbCursor.fetchone()
                            replace_data_price_his = \
                                (sysDate, sysDate,dbResult[0],sysDate,price)
                            self.addHouseInfoPriceHis(replace_data_price_his)
                        else:
                            if result[5] != price:
                                upHouseInfoSql = 'UPDATE T_HOUSE_INFO  SET LAST_UPDATE_DATE=%s,PRICE=%s WHERE HOUSE_ID=%s'
                                self.dbCursor.execute(upHouseInfoSql, (sysDate, price, result[0]))
                                self.db.commit()
                                replace_data_price_his = \
                                    (sysDate, sysDate, result[0], sysDate, price)
                                self.addHouseInfoPriceHis(replace_data_price_his)
                    else:
                        pass
                    # houseRoomSize = index.find('div', attrs={'class': 'house_type clearfix'}).get_text()
                    # houseRoomStyle = index.find('div', attrs={'class': 'house_type clearfix'}).find_all('a')
                    # for styleIndex in houseRoomStyle:
                    #     roomStyle = styleIndex.get_text()



                except Exception as error:
                    print("抓取数据失败。", error)


    def addHouseInfo(self,replace_data):
        replace_sql = '''REPLACE INTO
                              T_HOUSE_INFO(CREATION_DATE,LAST_UPDATE_DATE,HOUSE_NAME,ALIAS_NAME,
                              PRICE,AREA_ID,ADDRESS,CURRENT_SALE_INFO,SALE_TEL,SALE_FLAG,HOUSE_TAG,LON,
                              LAT)
                              VALUES(%s,%s,%s,%s,
                              %s,%s,%s,%s,%s,%s,%s,%s,%s)'''

        try:
            print("获取到数据：")
            print(replace_data)
            self.dbCursor.execute(replace_sql, replace_data)
            self.db.commit()
        except Exception as err:
            print("插入数据库出错")
            print(replace_data)
            self.db.rollback()
            print(err)
            traceback.print_exc()

    def addHouseInfoPriceHis(self,replace_data):
        replace_sql = '''REPLACE INTO
                              T_HOUSE_PRICE_HIS(CREATION_DATE,LAST_UPDATE_DATE,HOUSE_ID,PRICE_DATE,PRICE)
                              VALUES(%s,%s,%s,%s,%s)'''

        try:
            print("获取到addHouseInfoPriceHis数据：")
            print(replace_data)
            self.dbCursor.execute(replace_sql, replace_data)
            self.db.commit()
        except Exception as err:
            print("插入数据库出错")
            print(replace_data)
            self.db.rollback()
            print(err)
            traceback.print_exc()

    def run(self):
        print(self.name + "is running")
        self.getHouseListInfo()


if __name__ == '__main__':
    threads = []
    config = configparser.ConfigParser()
    config.read("area.ini")
    huangpu = config.get("guangzhou", "huangpu")
    huangpuHouse = GetHouseInfoFromFang(huangpu)
    threads.append(huangpuHouse)
    nansha = config.get("guangzhou", "nansha")
    nanshaHouse = GetHouseInfoFromFang(nansha)
    threads.append(nanshaHouse)
    zengcheng = config.get("guangzhou", "zengcheng")
    zengchengHouse = GetHouseInfoFromFang(zengcheng)
    threads.append(zengchengHouse)
    huadou = config.get("guangzhou", "huadou")
    huadouHouse = GetHouseInfoFromFang(huadou)
    threads.append(huadouHouse)

    for thread in threads:
        thread.start()
        thread.join()


