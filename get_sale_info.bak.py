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

class get_sale_info(threading.Thread):

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
    num_value_dict = {'/images/267d349cd7.gif':'1','/images/66efa2e558.gif':'2','/images/fb979c9fce.gif':'3',
                      '/images/c39d2e1455.gif':'4','/images/3e8437ebe8.gif':'5','/images/eaf321fd07.gif':'6',
                      '/images/7df2faaa96.gif':'7','/images/983eae74f7.gif':'8','/images/75eb9d75c1.gif':'9',
                      '/images/d9133be78c.gif':'0'}
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
                BS = BeautifulSoup(saleInfoIndex.content.decode(get_sale_info.CHARSET_DEFALUT, 'ignore'), "html.parser")
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
                    # 获取预售基本信息
                    self.getSaleBaseInfo(license_info_url, licenseId)
                    # 获取每天房间销售明细信息
                    self.getSaleDetailInfo(license_info_url, licenseId)
            except Exception as error:
                print("获取楼盘",houseResult[4],'销售信息失败。',error)

    def getVcode(self,image_code_url,randValue):
        try:
            baseImage = image_code_url
            randomid2 = random.random() * 10000000
            baseImage = baseImage + randValue + '&randomId=' + str(randomid2)
            print("image code url:", baseImage)
            captch = self.__session.get(baseImage, headers=self.headers, timeout=120)
            with open('captcha.jpg', 'wb') as f:
                f.write(captch.content)
                f.close()
            im = Image.open('captcha.jpg', 'r')
            vcode = pytesseract.image_to_string(im)
            return vcode
        except Exception as error:
            return self.getVcode(image_code_url,randValue)


    def getSaleBaseInfo(self,baseUrl,saleLicenseId):
        dataParams = baseUrl.split('?')[1].split('&')
        dataDict = {}
        for param in dataParams:
           paramValue =  param.split('=')
           dataDict[paramValue[0]] = paramValue[1]
        baseDetailUrl = 'http://g4c.laho.gov.cn/search/project/project.jsp?pjID='
        baseDetailUrl = baseDetailUrl + dataDict['pjID']
        baseInfoIndex = self.__session.post(baseDetailUrl, headers=self.headers, timeout=120)
        BS = BeautifulSoup(baseInfoIndex.content.decode(get_sale_info.CHARSET_DEFALUT, 'ignore'), "html.parser")
        tableDatas   = BS.find_all('table')
        trData = tableDatas[0].find_all('tr')
        td5Data = trData[5].find_all('td')
        canSoldNumData = td5Data[1].find_all('img')
        canSoldAreaData = td5Data[3].find_all('img')
        canSoldNum = ''
        canSoldArea = ''
        for num in canSoldNumData:
            value = num['src']
            canSoldNum = canSoldNum + self.num_value_dict.get(value)
            point = num.get_text()
            if point is not None:
                canSoldNum = canSoldNum + point

        for num in canSoldAreaData:
            value = num['src']
            canSoldArea = canSoldArea + self.num_value_dict.get(value)
            point = num.get_text()
            if point is not None:
                canSoldNum = canSoldNum + point

        td6Data = trData[6].find_all('td')
        soldNumData = td6Data[1].find_all('img')
        notSoldNumData = td6Data[3].find_all('img')
        soldNum = ''
        notSoldNum = ''
        for num in canSoldNumData:
            value = num['src']
            soldNum = soldNum + self.num_value_dict.get(value)
            point = num.get_text()
            if point is not None:
                canSoldNum = canSoldNum + point

        for num in notSoldNumData:
            value = num['src']
            notSoldNum = notSoldNum + self.num_value_dict.get(value)
            point = num.get_text()
            if point is not None:
                canSoldNum = canSoldNum + point

        td7Data = trData[7].find_all('td')
        soldAreaData = td7Data[1].find_all('img')
        notSoldAreaData = td7Data[3].find_all('img')
        soldAreaNum = ''
        notSoldAreaNum = ''
        for num in soldAreaData:
            value = num['src']
            soldAreaNum = soldAreaNum + self.num_value_dict.get(value)
            point = num.get_text()
            if point is not None:
                canSoldNum = canSoldNum + point

        for num in notSoldAreaData:
            value = num['src']
            notSoldAreaNum = notSoldAreaNum + self.num_value_dict.get(value)
            point = num.get_text()
            if point is not None:
                canSoldNum = canSoldNum + point


        trDetailData = tableDatas[1].find_all('tr')
        saleDate  = trDetailData[2].find('td',attrs={'id': 'currentDate'}).get_text()
        dayTdData = trDetailData[2].find_all('td')
        daySoldNumData = dayTdData[1].find_all('img')
        daySoldAreaData = dayTdData[2].find_all('img')
        dayRefundNumData = dayTdData[3].find_all('img')
        avervegePriceData = dayTdData[6].find_all('img')
        daySoldNum = ''
        daySoldArea = ''
        dayRefundNum = ''
        avervegePrice = ''
        for num in daySoldNumData:
            value = num['src']
            daySoldNum = daySoldNum + self.num_value_dict.get(value)
        for num in daySoldAreaData:
            value = num['src']
            daySoldArea = daySoldArea + self.num_value_dict.get(value)
        for num in dayRefundNumData:
            value = num['src']
            dayRefundNum = dayRefundNum + self.num_value_dict.get(value)
        for num in avervegePriceData:
            value = num['src']
            avervegePrice = avervegePrice + self.num_value_dict.get(value)
        sysDate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        replace_data = \
            (sysDate, sysDate,saleLicenseId, canSoldNum, canSoldArea, soldNum, soldAreaNum,
             notSoldNum, notSoldAreaNum, avervegePrice, saleDate,'1',daySoldNum,daySoldArea,dayRefundNum)
        self.saveOrUpdateSaleSumInfo(replace_data)


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

    def saveOrUpdateSaleSumInfo(self, replace_data):
            replace_sql = '''REPLACE INTO T_SALE_DAY_SUM_INFO(CREATION_DATE,LAST_UPDATE_DATE,LICENSE_ID,CAN_SOLD_ROOM_SUM,
                                           CAN_SOLD_AREA_SUM,SOLD_ROOM_SUM,SOLD_AREA_SUM,NOT_SOLD_ROOM_SUM,NOT_SOLD_AREA_SUM,
                                           AVERAGE_PRICE,SOLD_DATE,HOUSE_TYPE,SOLD_DAY_ROOM_NUM,SOLD_DAY_AREA_NUM,REFUND_DAY_ROOM_NUM)
                                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
            query_sql = '''SELECT * FROM T_SALE_DAY_SUM_INFO t WHERE t.SOLD_DATE=%s'''
            try:
                print("获取到数据：", replace_data)
                self.dbCursor.execute(query_sql, (replace_data[10]))
                result = self.dbCursor.fetchone()
                if result is None:
                    self.dbCursor.execute(replace_sql, replace_data)
                    self.db.commit()
            except Exception as err:
                print("插入数据库出错")
                print("获取到数据：")
                print(replace_data)
                self.db.rollback()
                print(err)
                traceback.print_exc()


    def getSaleDetailInfo(self,baseUrl,licenseId):
        dataParams = baseUrl.split('?')[1].split('&')
        dataDict = {}
        for param in dataParams:
            paramValue = param.split('=')
            dataDict[paramValue[0]] = paramValue[1]
        detailUrl = 'http://g4c.laho.gov.cn/search/project/sellForm.jsp?pjID='
        detailUrl = detailUrl + dataDict['pjID'] + '&presell='+ dataDict['preSell'] + '&chnlname=' + dataDict['name']
        detailInfoIndex = str(self.__session.post(detailUrl, headers=self.headers, timeout=120).text)
        tree = etree.HTML(detailInfoIndex)

        tdNodes = tree.xpath('/html/body/div')[0].xpath('form/table')[0].xpath('tr')[2].xpath('td/table/tr/td')
        for node in tdNodes:
            sysDate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            buildingNumNode  = node.xpath('input')[0]
            if buildingNumNode is not None:
                buildingAddr = buildingNumNode.tail
                buildingNum = buildingNumNode.xpath('@value')[0]
                build_data = \
                    (sysDate, sysDate, buildingNum, buildingAddr, licenseId)
                buildingId = self.saveOrUpdateBuildingInfo(build_data)
                self.getSaleDayDetailInfo(buildingId, buildingNum)




    def getSaleDayDetailInfo(self,buildingId,buildingNum):
        baseUrl = 'http://g4c.laho.gov.cn/search/project/sellForm_pic.jsp?chnlname=ysz'
        #查询房产每天销售明细信息
        data = {
                'modeID': 1,
                'hfID': 0,
                'unitType': 0,
                'houseStatusID': 0,
                'totalAreaID': 0,
                'inAreaID':0,
                'buildingID':buildingNum
            }
        dayDetailInfoIndex = self.__session.post(baseUrl, headers=self.headers, data=data,timeout=120).text
        tree = etree.HTML(dayDetailInfoIndex)
        trNodes = tree.xpath('/html/body/div/table/tr')
        index = 0
        saleDate = '2099-12-30' #默认销售时间
        for node in trNodes:
            index = index + 1
            if index <= 2:
                continue
            tdNodes = node.xpath('td')
            floorNum = tdNodes[0].text.strip()
            roomTdNodes = tdNodes[1].xpath('table/tr/td/table/tr/td')
            for rooTdNode in roomTdNodes:
                bgcolor = rooTdNode.xpath('@bgcolor')[0]
                roomNum = rooTdNode.xpath('a')[0].text.strip()
                roomInfo = str(rooTdNode.xpath('a')[0].xpath('@title')[0])
                roomInfoData = roomInfo.split('\n')
                roomDataDict = {}
                for roomData in roomInfoData:
                    value = roomData.split('：')
                    if (len(value) > 1):
                        roomDataDict[value[0]] = value[1]

                fontNode = rooTdNode.xpath('a')[0].xpath('font')
                dealStatus = ''
                if len(fontNode) > 0:
                    dealStatus = fontNode[0].text
                soldStatus = '99'
                if bgcolor == '#DB4923': #不可销售
                    soldStatus = '10'
                elif bgcolor=='#96C138': #预售销售
                    soldStatus = '20'
                roomStyle = roomDataDict['户型']
                saleArea = roomDataDict['总面积']
                useArea = roomDataDict['套内面积']
                sysDate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                add_data =\
                    (sysDate,sysDate,saleDate,floorNum,roomNum,soldStatus,dealStatus,buildingId,roomStyle,saleArea,useArea)
                self.saveOrupdateSaleDayDetailInfo(add_data)



    def saveOrUpdateBuildingInfo(self, replace_data):
        replace_sql = '''REPLACE INTO T_BUILDING_INFO(CREATION_DATE,LAST_UPDATE_DATE,BUILDING_NUM,ADDRESS,LICENSE_ID)
                            VALUES(%s,%s,%s,%s,%s)'''
        query_sql = '''SELECT * FROM T_BUILDING_INFO t WHERE t.BUILDING_NUM=%s'''
        try:
            print("获取到数据：", replace_data)
            self.dbCursor.execute(query_sql, (replace_data[2]))
            result = self.dbCursor.fetchone()
            if result is None:
                self.dbCursor.execute(replace_sql, replace_data)
                self.db.commit()
            self.dbCursor.execute(query_sql, (replace_data[2]))
            dbResult = self.dbCursor.fetchone()
            return dbResult[0]
        except Exception as err:
            print("插入数据库出错")
            print("获取到数据：")
            print(replace_data)
            self.db.rollback()
            print(err)
            traceback.print_exc()

    def saveOrupdateSaleDayDetailInfo(self, replace_data):
        replace_sql = '''REPLACE INTO T_SALE_DAY_DETAIL_INFO(CREATION_DATE,LAST_UPDATE_DATE,SALE_DATE,FLOOR_NUM,
                         ROOM_NUM,SOLD_STATUS,DEAL_STATUS,BUILDING_ID,ROOM_STYLE,SALE_AREA,USE_AREA)
                            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
        query_sql = '''SELECT * FROM T_SALE_DAY_DETAIL_INFO t WHERE t.BUILDING_ID=%s AND t.ROOM_NUM=%s'''
        upate_sql = '''UPDATE T_SALE_DAY_DETAIL_INFO t SET t.SOLD_STATUS=%s,t.SALE_DATE=%s,t.DEAL_STATUS=%s 
                        WHERE t.BUILDING_ID=%s AND t.ROOM_NUM=%s '''
        try:
            print("获取到数据：", replace_data)
            self.dbCursor.execute(query_sql, (replace_data[7],replace_data[4]))
            result = self.dbCursor.fetchone()
            if result is None:
                self.dbCursor.execute(replace_sql, replace_data)
                self.db.commit()
            else:
                if result[5] != replace_data[5] and replace_data[5]==10:
                    saleDate = datetime.datetime.now().strftime("%Y-%m-%d")
                    self.dbCursor.execute(upate_sql, (replace_data[5],saleDate,replace_data[6],replace_data[7],replace_data[3]))

        except Exception as err:
            print("插入数据库出错")
            print("获取到数据：")
            print(replace_data)
            self.db.rollback()
            print(err)
            traceback.print_exc()


    def run(self):
        print(self.name + "is running")
        self.getSaleInfo()


if __name__ == '__main__':
    saleInfo = get_sale_info()
    saleInfo.start()
    saleInfo.join()