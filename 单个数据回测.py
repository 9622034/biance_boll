#! /usr/bin/python
# -*- codeing = utf-8 -*-
# @Time : 2021-09-16 8:09
# @Author : yjh
# @File : 单个数据回测.py
# @Software : PyCharm
import pandas as pd
from  Signal import *
from test_bolling import *
pd.set_option('display.max_columns',None)
pd.set_option('display.max_rows',None)
pd.set_option('display.width', 5000)

df = pd.DataFrame()
# 导入
df = pd.read_csv('D:\pythonProject\币安爬虫\ETHUSDT_15m_2021-10-03_2021-10-11.csv')
para = [158,2]
# x = 0.03
signal_bolliing(df,para)
# signal_bolling_tp(df,para,x)
print(equity_curve_with_long_and_short(df))
# df.to_csv('./shuju3')