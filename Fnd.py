#! /usr/bin/python
# -*- codeing = utf-8 -*-
# @Time : 2021-09-11 16:55
# @Author : yjh
# @File : fFnd.py
# @Software : PyCharm

import pandas as pd
from  Signal import *
from test_bolling import *
pd.set_option('display.max_columns',None)
pd.set_option('display.max_rows',None)
pd.set_option('display.width', 5000)


df = pd.DataFrame()
# 导入
df = pd.read_csv('D:\pythonProject\币安爬虫\ETHUSDT_15m_2021-01-01_2021-10-02.csv')

m_list = range(157,159)
n_list = [2]


rtn = pd.DataFrame()
for m in m_list:
    for n in n_list:
        para = [m,n]


# 计算信号
# para = [210,3]
        signal_bolliing(df,para)

        # 计算资金曲线
        # 判断交易次数
        x = 0
        for i in range(len(df)):
           if df.loc[i]['signal'] ==1 or df.loc[i]['signal']==-1:
               x += 1
        df = equity_curve_with_long_and_short(df.copy())
        print(m,"--",n,"策略最终收益:",df.iloc[-1]['equity_curve'],x)
        rtn.loc[str(para),'收益'] = df.iloc[-1]['equity_curve']
print(rtn.sort_values(by='收益',ascending=False))