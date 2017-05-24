#!/usr/bin/python
# -*- coding: UTF-8 -*-
import pymysql
import configparser
import  sys

class db_connection:

    @classmethod
    def init(cls):
        # 获取配置文件
        config = configparser.ConfigParser()
        config.read("config.ini")
        # 初始化数据库连接
        try:
            db_host = config.get("db", "host")
            db_port = int(config.get("db", "port"))
            db_user = config.get("db", "user")
            db_pass = config.get("db", "password")
            db_db = config.get("db", "db")
            db_charset = config.get("db", "charset")
            db = pymysql.connect(host=db_host, port=db_port, user=db_user, passwd=db_pass, db=db_db,
                                      charset=db_charset)
            return  db
        except:
            print("请检查数据库配置")
            sys.exit()

    @classmethod
    def get_db(cls):
        return db_connection.init()

    @classmethod
    def get_db_cursor(self):
        return db_connection.get_db().cursor()

if __name__ == '__main__':
    print(db_connection.get_db().cursor().execute())
