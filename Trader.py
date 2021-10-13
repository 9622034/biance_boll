#! /usr/bin/python
# -*- codeing = utf-8 -*-
# @Time : 2021-09-09 14:25
# @Author : yjh
# @File : Trader.py
# @Software : PyCharm
import ccxt
import datetime
import time
import pandas as pd
from email.mime.text import MIMEText
from smtplib import SMTP

def next_run_time(time_interval,ahead_time=1):
    if time_interval.endswith('m'):
        nowtime = datetime.datetime.now()
        interval = int(time_interval.strip('m'))
        target_min = ((int(nowtime.minute / interval)) + 1 ) *interval
        if target_min < 60:
            target_time = nowtime.replace(minute=target_min,second=0,microsecond=0)
        else:
            if nowtime.hour == 23:
                target_time = nowtime.replace(hour=0,minute=0,second=0,microsecond=0)
                target_time += datetime.timedelta(days=1)
            else:
                target_time = nowtime.replace(hour=nowtime.hour+1,minute=0,second=0,microsecond=0)

        if (target_time - datetime.datetime.now()).seconds < ahead_time+1:
            print("距离target_time不足",ahead_time,"秒下次再运行")
            target_time += datetime.timedelta(interval)
        print("下次运行时间",target_time)
        return target_time
    else:
        exit("please use 'm' to calculate time")

def get_binance_candle_data(exchange,symbol,time_interval):
    # 抓取数据
    content = exchange.fetch_ohlcv(symbol=symbol,timeframe=time_interval,limit=100)
    df = pd.DataFrame(content, dtype=float)
    df.rename(columns={
        0: 'MTS', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'
    }, inplace=True)  # 重命名
    df['candle_begin_time'] = pd.to_datetime(df['MTS'], unit='ms')
    df['candle_begin_time_GMT8'] = df['candle_begin_time'] + datetime.timedelta(hours=8)  # 换成东八区时间
    df = df[['candle_begin_time_GMT8', 'open', 'high', 'low', 'close', 'volume']]
    return df


def get_binance_contract_candadle(exchange,pair,type,interval,limit):
    content = exchange.fapiPublic_get_continuousklines(
        {
            'pair':pair,'contractType':type,'interval':interval,'limit':limit
        } # limit 是int型
    )
    df = pd.DataFrame(content, dtype=float)
    df.rename(columns={
        0: 'MTS', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'
    }, inplace=True)  # 重命名
    df['candle_begin_time'] = pd.to_datetime(df['MTS'], unit='ms')
    df['candle_begin_time_GMT8'] = df['candle_begin_time'] + datetime.timedelta(hours=8)  # GMT是格林威治标准时间
    df = df[['candle_begin_time_GMT8', 'open', 'high', 'low', 'close', 'volume']]
    return df
"""
合约类型:
PERPETUAL 永续合约
CURRENT_MONTH 当月交割合约
NEXT_MONTH 次月交割合约
CURRENT_QUARTER 当季交割合约
NEXT_QUARTER 次季交割合约
"""


def signal_bolling(df,para):
    n = para[0] # 移动平均线的天数
    m = para[1] # 系数

    # 中轨
    df['median'] = df['close'].rolling(n, min_periods=1).mean()
    # 上下轨
    df['std'] = df['close'].rolling(n, min_periods=1).std(ddof=0)  # ddof=0表示标准差
    df['upper'] = df['median'] + m * df['std']
    df['lower'] = df['median'] - m * df['std']
    # 获得做多信号
    condition1 = df['close'] > df['upper']
    condition2 = df['close'].shift(1) <= df['upper'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1  # 将做多的信号设置为1
    # 做多平仓信号
    condition1 = df['close'] < df['median']
    condition2 = df['close'].shift(1) >= df['median'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0  # 将做多平仓信号设置为0
    # 做空信号
    condition1 = df['close'] < df['lower']
    condition2 = df['close'].shift(1) >= df['lower'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1  # 将做空的信号设置为-1
    # 做空平仓信号
    condition1 = df['close'] > df['median']
    condition2 = df['close'].shift(1) <= df['median'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0  # 将做空平仓信号设置为0
    # 合并多空信号,去除重负信号 ,不可能存在同时开多开空的信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, skipna=True,min_count=1)
    temp = df[df['signal'].notnull()][['signal']]  # 去掉空值的行,只留下有信号的
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']
    df.drop(['median', 'upper', 'lower', 'std', 'signal_long', 'signal_short'], axis=1, inplace=True)
    return df

# 获取合约仓位
def get_perpetualContract_position(exchange,symbol):
    Contract_dic={
        'SUSHIUSDT': 1,'CVCUSDT': 2,'BTSUSDT': 3,'HOTUSDT': 4,'ZRXUSDT': 5,'QTUMUSDT': 6,'IOTAUSDT': 7,'BTCBUSD': 8,'WAVESUSDT': 9,
        'ADAUSDT': 10,'LITUSDT': 11,'XTZUSDT': 12,'BNBUSDT': 13,'AKROUSDT': 14,'HNTUSDT': 15,'ETCUSDT': 16,'XMRUSDT': 17,'YFIUSDT': 18,'FTTBUSD': 19,
        'ETHUSDT': 20,'ALICEUSDT': 21,'ALPHAUSDT': 22, 'SFPUSDT': 23,'REEFUSDT': 24,'BATUSDT': 25,'DOGEUSDT': 26,'TRXUSDT': 27,
        'RLCUSDT': 28,'BTCSTUSDT': 29,'STORJUSDT': 30,'SNXUSDT': 31,'AUDIOUSDT': 32,'XLMUSDT': 33,'IOTXUSDT': 34,'NEOUSDT': 35,'UNFIUSDT': 36,'SANDUSDT': 37,
        'DASHUSDT': 38,'KAVAUSDT': 39,'RUNEUSDT': 40,'CTKUSDT': 41,'LINKUSDT': 42,'CELRUSDT': 43,'RSRUSDT': 44,'ADABUSD': 45,
        'DGBUSDT': 46,'SKLUSDT': 47,'RENUSDT': 48,'TOMOUSDT': 49,'MTLUSDT': 50,'LTCUSDT': 51,'DODOUSDT': 52,'EGLDUSDT': 53,'KSMUSDT': 54,'BNBBUSD': 55,'ONTUSDT': 56,'VETUSDT': 57,'TRBUSDT': 58,'MANAUSDT': 59,'COTIUSDT': 60,'CHRUSDT': 61,
        'ETHUSDT_210924':62,'BAKEUSDT': 63,'GRTUSDT': 64,'FLMUSDT': 65,'MASKUSDT': 66,'EOSUSDT': 67,'OGNUSDT': 68,'SCUSDT': 69,'BALUSDT': 70,'STMXUSDT': 71,'BTTUSDT': 72,'LUNAUSDT': 73,'DENTUSDT': 74,'KNCUSDT': 75,'SRMUSDT': 76,'ENJUSDT': 77,'C98USDT': 78,'ZENUSDT': 79,'ATOMUSDT': 80,'NEARUSDT': 81,'SOLBUSD': 82,'BCHUSDT': 83,'ATAUSDT': 84,'IOSTUSDT': 85,
        'HBARUSDT': 86,'ZECUSDT': 87,'1000SHIBUSDT':88,'TLMUSDT': 89,'BZRXUSDT': 90,'ETHBUSD': 91,'AAVEUSDT': 92,'GTCUSDT': 93,'ALGOUSDT': 94,'ICPUSDT': 95,'BTCUSDT_210924': 96,'LRCUSDT': 97,'AVAXUSDT': 98,'MATICUSDT': 99,'1INCHUSDT': 100,'MKRUSDT': 101,'THETAUSDT': 102,'UNIUSDT': 103,'LINAUSDT': 104,'RVNUSDT': 105,
        'FILUSDT': 106,'NKNUSDT': 107,'DEFIUSDT': 108,'COMPUSDT': 109,'BTCDOMUSDT': 110,'SOLUSDT': 111,'BTCUSDT': 112,'OMGUSDT': 113,'ICXUSDT': 114,'BLZUSDT': 115,'FTMUSDT': 116,'YFIIUSDT': 117,'KEEPUSDT': 118,'BANDUSDT': 119,'XRPBUSD': 120,'DOGEBUSD': 121,
        'XRPUSDT': 122,'SXPUSDT': 123,'CRVUSDT': 124,'BELUSDT': 125,'DOTUSDT': 126,'XEMUSDT': 127,'ONEUSDT': 128,'ZILUSDT': 129,'AXSUSDT': 130,'DYDXUSDT': 131,'OCEANUSDT': 132,'CHZUSDT': 133,'ANKRUSDT': 134,
    }
    num = Contract_dic[symbol]
    positionAmt = float(exchange.fapiPrivate_get_account()['positions'][num]['positionAmt']) # 有正负
    return positionAmt

def get_contractAccount_balance(exchange,base_coin):
    dic={'BNB':0,'USDT':1,'BUSD':2}
    num = dic[base_coin]
    asset =  float(exchange.fapiPrivate_get_account()['assets'][num]['walletBalance'])
    return asset

# 下单函数
def place_order(exchange,pair,side,Order_type,price,quantity):
    for i in range(5):
        try:
            # 限价单
            if Order_type == 'LIMIT':
                if side == 'BUY':
                    order_info = exchange.fapiPrivate_post_order({
                        'symbol': pair,'side': 'BUY',  'type': 'LIMIT','price': price,
                        'quantity': quantity,  'timeInForce': 'GTC',
                        # DAY（日内）GTC（取消前有效）OPG（第二天开盘提交）IOC（立刻执行或取消）FOK（全数执行或立即取消）DTC（日内直到取消）
                                        }
                                    )
                elif side == 'SELL':
                    order_info = exchange.fapiPrivate_post_order({
                        'symbol': pair, 'side': 'SELL', 'type': 'LIMIT', 'price': price,
                        'quantity': quantity,'timeInForce': 'GTC',})
            # 市价单
            elif Order_type == 'MARKET':
                if side == 'BUY':
                    order_info = exchange.fapiPrivate_post_order({
                        'symbol': pair, 'side': 'BUY', 'type': 'MARKET',
                        'quantity': quantity, 'timeInForce': 'GTC',})
                elif side == 'SELL':
                    order_info = exchange.fapiPrivate_post_order({
                        'symbol': pair, 'side': 'BUY', 'type': 'MARKET',
                        'quantity': quantity, 'timeInForce': 'GTC', })
            else:
                pass
            print("下单成功",Order_type,side,pair,price,quantity)
            print("下单信息",order_info,"\n")
            return order_info
        except Exception as e:
            print("下单错误,1秒后重试",e)
            time.sleep(1)
    print("程序错误超过5次,退出")
    exit()

# 获取交易深度价格(买一价卖一价)
def get_price(exchange,side,pair):
    if side == 'SELL':
        price = float(exchange.fapiPublic_get_depth({'symbol': pair, 'limit': 5})['bids'][0][0])
    elif side == 'BUY':
        price = float(exchange.fapiPublic_get_depth({'symbol': pair, 'limit': 5})['asks'][0][0])
    return price