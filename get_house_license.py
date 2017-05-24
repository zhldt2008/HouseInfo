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
from PIL import  Image
import pytesseract
import time
import json
import http.cookiejar as cookielib
from db_connection import  db_connection
import  os
from lxml import etree
import random

class get_house_license(threading.Thread):

    __session = ''
    CHARSET_DEFALUT = 'gb2312'
    db = ''
    dbCursor = ''
    contextPath = 'http://g4c.laho.gov.cn'

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Upgrade-Insecure-Requests": "1",
        "Content-Type": "application/x-www-form-urlencoded; charset=gb2312",
        "Pragma": "no-cache",
        "Accept-Encoding": "gzip, deflate, br",
        'Connection': 'close'
    }

    def __init__(self):
        threading.Thread.__init__(self)
        os.environ.setdefault('TESSDATA_PREFIX', 'C:/Program Files (x86)/Tesseract-OCR')
        self.db = db_connection.get_db()
        self.dbCursor = self.db.cursor()
        requests.adapters.DEFAULT_RETRIES = 5
        self.__session = requests.Session()
        self.__session.cookies = cookielib.LWPCookieJar(filename='cookie')
        self.__session.keep_alive = False
        try:
            self.__session.cookies.load(ignore_discard=True)
        except Exception as error:
            print('Cookie 未能加载',error)

    def getSaleInfo(self):
        search_url = 'http://housing.gzcc.gov.cn/search/presell/preSellSearch.jsp'
        rand_base_url = 'http://housing.gzcc.gov.cn/search/generateRand.jsp?randomId='
        image_code_url = 'http://housing.gzcc.gov.cn/search/generateImage.jsp?rand='
       #查询所有房产信息
        query_house_sql = 'SELECT * FROM T_HOUSE_INFO'
        self.dbCursor.execute(query_house_sql)
        houseResultList =self.dbCursor.fetchall()
        for houseResult in houseResultList:
            try :
                randomid = random.random() * 10000000
                rand_url = rand_base_url + str(randomid)
                print("rand_url:", rand_url)
                rand = self.__session.get(rand_url, headers=self.headers, timeout=120)
                rand = rand.content.decode('utf-8')
                randArray = rand.split('=')
                randValue = randArray[0].strip()
                randInput = randArray[1].strip()
                self.__session.cookies.save()
                # 获取验证码
                vcode = ''
                try:
                    vcode = self.getVcode(image_code_url, randValue)
                except:
                    vcode = self.getVcode(image_code_url, randValue)
                # 查询房产信息
                data = {
                    'projectName': houseResult[4].encode('gb2312'),
                    'imgvalue': vcode,
                    'yszrandinput': randInput,
                    'chnlname': '预售证'.encode('gb2312'),
                    'Submit': '查询'.encode('gb2312')
                }
                houseId = houseResult[0]
                saleInfoIndex = self.__session.post(search_url, headers=self.headers, data=data, timeout=120)
                BS = BeautifulSoup(saleInfoIndex.content.decode(get_house_license.CHARSET_DEFALUT, 'ignore'), "html.parser")
                trData = BS.find('table', attrs={'id': 'tab'}).find_all('tr')
                index = 0
                # 取第一条预售证信息
                sale_license_num = ''
                sale_project_name = ''
                sale_company = ''
                house_num = ''
                room_total_num = ''
                room_total_area = ''
                sale_license_date = ''
                license_info_url = ''
                if len(trData) >1:
                    tr = trData[1]
                    tdData = tr.find_all('td')
                    tdindex = 0
                    for td in tdData:
                        if tdindex == 1:
                            sale_license_num = td.find('a').get_text()
                        if tdindex == 2:
                            sale_project_name = td.find('a').get_text()
                            license_info_url = td.find('a')['href']
                        if tdindex == 3:
                            sale_company = td.find('a').get_text()
                        if tdindex == 4:
                            house_num = td.find('a').get_text()
                        if tdindex == 5:
                            room_total_num = td.find('a').get_text()
                        if tdindex == 6:
                            room_total_area = td.find('a').get_text()
                        if tdindex == 7:
                            sale_license_date = td.find('a').get_text()
                        tdindex = tdindex + 1

                    sysDate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    replace_data = \
                       (sysDate, sysDate, houseId, sale_license_num, sale_project_name, sale_company, house_num,
                        room_total_num, room_total_area, sale_license_date, pymysql.escape_string(license_info_url))
                    # 将预售信息插入数据库
                    licenseId = self.saveOrUpdateLicense(replace_data)
                else:
                    print("未获取到楼盘：",houseResult[4],'，license信息失败。')
            except Exception as error:
                print("获取楼盘：",houseResult[4],'，license信息失败。',error)

    def getVcode(self,image_code_url,randValue):
        try:
            baseImage = image_code_url
            randomid2 = random.random() * 10000000
            baseImage = baseImage + randValue + '&randomId=' + str(randomid2)
            print("image code url:", baseImage)
            captch = self.__session.get(baseImage, headers=self.headers, timeout=120)
            self.__session.cookies.save()
            with open('captcha.jpg', 'wb') as f:
                f.write(captch.content)
                f.close()
            im = Image.open('captcha.jpg', 'r')
            vcode = pytesseract.image_to_string(im)
            return vcode
        except Exception as error:
            return self.getVcode(image_code_url,randValue)




    def saveOrUpdateLicense(self,replace_data):
        replace_sql = '''REPLACE INTO T_HOUSE_LICENSE(CREATION_DATE,LAST_UPDATE_DATE,HOUSE_ID,LICENSE_NUM,
                                       PROJECT_NAME,SALE_COMPANY,HOUSE_TOTAL_NUM,ROOM_TOTAL_NUM,TOTAL_AREA,LICENSE_DATE,DETAIL_URL)
                                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
        query_sql = '''SELECT * FROM T_HOUSE_LICENSE t WHERE t.license_num =%s'''
        try:
            print("获取到houseLicense数据：",replace_data)
            self.dbCursor.execute(query_sql, (replace_data[3]))
            result = self.dbCursor.fetchone()
            if result is  None:
              self.dbCursor.execute(replace_sql, replace_data)
              self.db.commit()
            self.dbCursor.execute(query_sql, (replace_data[3]))
            dbResult = self.dbCursor.fetchone()
            return dbResult[0]
        except Exception as err:
            print("插入数据库出错",err)
            self.db.rollback()
            traceback.print_exc()



    def run(self):
        print(self.name + "is running")
        self.getSaleInfo()


if __name__ == '__main__':
    license = get_house_license()
    license.start()
    license.join()