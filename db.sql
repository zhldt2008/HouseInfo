/*
SQLyog Ultimate v11.33 (64 bit)
MySQL - 5.7.15 : Database - house
*********************************************************************
*/

/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
CREATE DATABASE /*!32312 IF NOT EXISTS*/`house` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `house`;

/*Table structure for table `T_AREA` */

CREATE TABLE `T_AREA` (
  `AREA_ID` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `CREATION_DATE` datetime DEFAULT NULL COMMENT '创建时间',
  `LAST_UPDATE_DATE` datetime DEFAULT NULL COMMENT '修改时间',
  `AREA_TYPE` char(2) NOT NULL COMMENT '类型',
  `AREA_NAME` varchar(64) NOT NULL COMMENT '名称',
  `CODE` varchar(64) DEFAULT NULL COMMENT '编码',
  `PARENT_AREA_ID` bigint(20) NOT NULL,
  PRIMARY KEY (`AREA_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=1007 DEFAULT CHARSET=utf8 COMMENT='地区表';

/*Table structure for table `T_BUILDING_INFO` */

CREATE TABLE `T_BUILDING_INFO` (
  `BUILDING_ID` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `CREATION_DATE` datetime DEFAULT NULL COMMENT '创建时间',
  `LAST_UPDATE_DATE` datetime DEFAULT NULL COMMENT '修改时间',
  `BUILDING_NUM` varchar(128) DEFAULT NULL COMMENT '楼盘NUM',
  `ADDRESS` varchar(256) DEFAULT NULL COMMENT '楼盘详细地址',
  `LICENSE_ID` bigint(20) DEFAULT NULL COMMENT '销售许可ID',
  PRIMARY KEY (`BUILDING_ID`),
  KEY `FK_Reference_5` (`LICENSE_ID`),
  CONSTRAINT `FK_Reference_5` FOREIGN KEY (`LICENSE_ID`) REFERENCES `T_HOUSE_LICENSE` (`LICENSE_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=910 DEFAULT CHARSET=utf8 COMMENT='楼盘每栋房子信息';

/*Table structure for table `T_HOUSE_INFO` */

CREATE TABLE `T_HOUSE_INFO` (
  `HOUSE_ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `CREATION_DATE` datetime DEFAULT NULL COMMENT '创建时间',
  `LAST_UPDATE_DATE` datetime DEFAULT NULL COMMENT '修改时间',
  `HOUSE_NAME` varchar(32) DEFAULT NULL COMMENT '楼盘名称',
  `ALIAS_NAME` varchar(32) DEFAULT NULL COMMENT '楼盘别名',
  `PRICE` double DEFAULT NULL COMMENT '价格',
  `AREA_ID` bigint(20) DEFAULT NULL COMMENT '地区ID',
  `ADDRESS` varchar(128) DEFAULT NULL COMMENT '地址',
  `CURRENT_SALE_INFO` varchar(128) DEFAULT NULL COMMENT '最新开盘信息',
  `SALE_TEL` varchar(128) DEFAULT NULL COMMENT '售楼电话',
  `SALE_FLAG` char(2) DEFAULT NULL COMMENT '是否在售',
  `HOUSE_TAG` varchar(128) DEFAULT NULL COMMENT '房子优势标签',
  `LON` varchar(128) DEFAULT NULL COMMENT '经度',
  `LAT` varchar(128) DEFAULT NULL COMMENT '纬度',
  PRIMARY KEY (`HOUSE_ID`),
  KEY `FK_Reference_1` (`AREA_ID`),
  CONSTRAINT `FK_Reference_1` FOREIGN KEY (`AREA_ID`) REFERENCES `T_AREA` (`AREA_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=235 DEFAULT CHARSET=utf8 COMMENT='楼盘信息表';

/*Table structure for table `T_HOUSE_LICENSE` */

CREATE TABLE `T_HOUSE_LICENSE` (
  `LICENSE_ID` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `HOUSE_ID` bigint(20) DEFAULT NULL COMMENT '楼盘ID',
  `CREATION_DATE` datetime DEFAULT NULL COMMENT '创建时间',
  `LAST_UPDATE_DATE` datetime DEFAULT NULL COMMENT '修改时间',
  `LICENSE_NUM` varchar(12) DEFAULT NULL COMMENT '许可证编号',
  `PROJECT_NAME` varchar(64) DEFAULT NULL COMMENT '所属项目名称',
  `SALE_COMPANY` varchar(64) DEFAULT NULL COMMENT '开发商',
  `HOUSE_TOTAL_NUM` int(11) DEFAULT NULL COMMENT '预售棟数',
  `ROOM_TOTAL_NUM` int(11) DEFAULT NULL COMMENT '预售总套数',
  `TOTAL_AREA` decimal(10,0) DEFAULT NULL COMMENT '预售总面积',
  `LICENSE_DATE` datetime DEFAULT NULL COMMENT 'f发证日期',
  `DETAIL_URL` varchar(256) DEFAULT NULL COMMENT '明细URL',
  PRIMARY KEY (`LICENSE_ID`),
  KEY `FK_Reference_7` (`HOUSE_ID`),
  CONSTRAINT `FK_Reference_7` FOREIGN KEY (`HOUSE_ID`) REFERENCES `T_HOUSE_INFO` (`HOUSE_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=58 DEFAULT CHARSET=utf8 COMMENT='楼盘预售证信息';

/*Table structure for table `T_HOUSE_PRICE_HIS` */

CREATE TABLE `T_HOUSE_PRICE_HIS` (
  `PRICE_HIS_ID` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `CREATION_DATE` datetime DEFAULT NULL COMMENT '创建时间',
  `LAST_UPDATE_DATE` datetime DEFAULT NULL COMMENT '修改时间',
  `HOUSE_ID` bigint(20) DEFAULT NULL COMMENT '楼盘ID',
  `PRICE_DATE` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '价格时间',
  `PRICE` double DEFAULT NULL COMMENT '价格',
  PRIMARY KEY (`PRICE_HIS_ID`),
  KEY `FK_Reference_3` (`HOUSE_ID`),
  CONSTRAINT `FK_Reference_3` FOREIGN KEY (`HOUSE_ID`) REFERENCES `T_HOUSE_INFO` (`HOUSE_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=234 DEFAULT CHARSET=utf8 COMMENT='楼盘价格历史信息表';

/*Table structure for table `T_ROOM_STYLE` */

CREATE TABLE `T_ROOM_STYLE` (
  `ROOM_STYLE_ID` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `CREATION_DATE` datetime DEFAULT NULL COMMENT '创建时间',
  `LAST_UPDATE_DATE` datetime DEFAULT NULL COMMENT '修改时间',
  `ROOM_NAME` varchar(128) DEFAULT NULL,
  `HOUSE_ID` bigint(20) DEFAULT NULL,
  `ROOM_SIZE` varchar(32) DEFAULT NULL COMMENT '面积',
  `MAIN_ROOM_FALG` char(2) DEFAULT NULL COMMENT '是否主力户型',
  PRIMARY KEY (`ROOM_STYLE_ID`),
  KEY `FK_Reference_2` (`HOUSE_ID`),
  CONSTRAINT `FK_Reference_2` FOREIGN KEY (`HOUSE_ID`) REFERENCES `T_HOUSE_INFO` (`HOUSE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='房型信息表';

/*Table structure for table `T_SALE_DAY_DETAIL_INFO` */

CREATE TABLE `T_SALE_DAY_DETAIL_INFO` (
  `DETAIL_INFO_ID` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `CREATION_DATE` datetime DEFAULT NULL COMMENT '创建时间',
  `LAST_UPDATE_DATE` datetime DEFAULT NULL COMMENT '修改时间',
  `SALE_DATE` datetime DEFAULT NULL COMMENT '销售时间',
  `FLOOR_NUM` varchar(16) DEFAULT NULL COMMENT '楼层',
  `ROOM_NUM` varchar(16) DEFAULT NULL COMMENT '房号',
  `SOLD_STATUS` char(2) DEFAULT NULL COMMENT '房间状态',
  `DEAL_STATUS` char(2) DEFAULT NULL COMMENT '交易状态',
  `BUILDING_ID` bigint(20) DEFAULT NULL COMMENT '每栋房建筑ID',
  `ROOM_STYLE` varchar(12) DEFAULT NULL COMMENT '户型',
  `SALE_AREA` varchar(12) DEFAULT NULL COMMENT '销售面积',
  `USE_AREA` varchar(12) DEFAULT NULL COMMENT '使用面积',
  PRIMARY KEY (`DETAIL_INFO_ID`),
  KEY `FK_Reference_6` (`BUILDING_ID`),
  CONSTRAINT `FK_Reference_6` FOREIGN KEY (`BUILDING_ID`) REFERENCES `T_BUILDING_INFO` (`BUILDING_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=28769 DEFAULT CHARSET=utf8 COMMENT='楼盘每日销售明细表';

/*Table structure for table `T_SALE_DAY_SUM_INFO` */

CREATE TABLE `T_SALE_DAY_SUM_INFO` (
  `SUM_INFO_ID` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `CREATION_DATE` datetime DEFAULT NULL COMMENT '创建时间',
  `LAST_UPDATE_DATE` datetime DEFAULT NULL COMMENT '修改时间',
  `LICENSE_ID` bigint(20) DEFAULT NULL COMMENT '许可证ID',
  `CAN_SOLD_ROOM_SUM` int(11) DEFAULT NULL COMMENT '批准销售套数',
  `CAN_SOLD_AREA_SUM` double DEFAULT NULL COMMENT '批准销售面积',
  `SOLD_ROOM_SUM` int(11) DEFAULT NULL COMMENT '已经销售套数',
  `SOLD_AREA_SUM` double DEFAULT NULL COMMENT '已经销售面积',
  `NOT_SOLD_ROOM_SUM` int(11) DEFAULT NULL COMMENT '未销售套数',
  `NOT_SOLD_AREA_SUM` double DEFAULT NULL COMMENT '未销售面积',
  `AVERAGE_PRICE` double DEFAULT NULL COMMENT '销售均价',
  `SOLD_DATE` date DEFAULT NULL COMMENT '销售日期',
  `HOUSE_TYPE` char(2) DEFAULT NULL COMMENT '销售房屋类型',
  `SOLD_DAY_ROOM_NUM` int(11) DEFAULT NULL COMMENT '当日已售套数',
  `SOLD_DAY_AREA_NUM` double DEFAULT NULL COMMENT '当日已经销售面积',
  `REFUND_DAY_ROOM_NUM` int(11) DEFAULT NULL COMMENT '当日退房套数',
  PRIMARY KEY (`SUM_INFO_ID`),
  KEY `FK_Reference_8` (`LICENSE_ID`),
  CONSTRAINT `FK_Reference_8` FOREIGN KEY (`LICENSE_ID`) REFERENCES `T_HOUSE_LICENSE` (`LICENSE_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8 COMMENT='楼盘每日销售汇总表';

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
