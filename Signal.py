#! /usr/bin/python
# -*- codeing = utf-8 -*-
# @Time : 2021-09-11 16:44
# @Author : yjh
# @File : Signal.py
# @Software : PyCharm
import pandas as pd

def signal_bolliing(df,para):
    # df['candle_begin_time'] = pd.to_datetime(df['candle_begin_time'],unit='ms')
    # 设置参数
    n = para[0]  # 移动平均线
    m = para[1]  # 系数

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
    # print(df)

    # 做空信号
    condition1 = df['close'] < df['lower']
    condition2 = df['close'].shift(1) >= df['lower'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1  # 将做空的信号设置为-1

    # 做空平仓信号
    condition1 = df['close'] > df['median']
    condition2 = df['close'].shift(1) <= df['median'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0  # 将做空平仓信号设置为0


    # 去掉重复的看看有几种组合
    # df.drop_duplicates(subset=['signal_long','signal_short'],inplace=True) # 去除重复信号
    # print(df)
    # exit()

    # 合并多空信号,去除重负信号 ,不可能存在同时开多开空的信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, skipna=True,min_count=1)  # https://blog.csdn.net/zxstone/article/details/90680635

    # temp = df
    # # 做多止盈
    # for i in range(len(temp)):
    #     if temp.loc[i]['signal'] == 1:
    #         x = i + 1
    #         a = temp.loc[x]['open']  # 记录下一次开盘价 也就是真实的开仓价格
    #         while temp.loc[x]['signal'] != 0:  # 从开仓价那行往下 每行的open和开仓价算出收益率
    #             if temp.loc[x]['open'] / a - 1 >= 0.1:
    #                 temp.loc[temp.loc[x]['open']/a-1>=0.1,'signal']=0
    #                 # df.signal=0
    #                 # temp.loc[x]['signal'] = 0
    #                 break
    #             else:
    #                 x += 1
    #
    # temp.drop(['median', 'upper', 'lower', 'std', 'signal_long', 'signal_short'], axis=1, inplace=True)
    # print(temp)
    # exit()



    temp = df[df['signal'].notnull()][['signal']]  # 去掉空值的行,只留下有信号的
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    # print(temp)
    # exit()

    df['signal'] = temp['signal']
    df.drop(['median', 'upper', 'lower', 'std', 'signal_long', 'signal_short'], axis=1, inplace=True)
    # print(df)
    # exit()



    # 由signal计算出实际每天持有的仓位
    # 由于是收盘价产生的信号, 我们买入时是以第二根k线的开盘价买入
    df['pos'] = df['signal'].shift(1)  # signal信号往下挪一行才是实际仓位
    df['pos'].fillna(method='ffill', inplace=True)  # 向上补全空值(空值往上走遇到不是空值的A值,就用A值补全)
    df['pos'].fillna(value=0, inplace=True)  # 将初始行数的position补全为0



    # print(df)
    # 目录下输出了results.h5 后面计算资金曲线要导入
    # df.to_hdf(
    #     'D:\\results\\ADAresults.h5', key='all_data', mode='w'
    # )

def signal_bolling_tp(df,para,x):
    n = para[0]  # 移动平均线
    m = para[1]  # 系数

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

    # 做空信号
    condition1 = df['close'] < df['lower']
    condition2 = df['close'].shift(1) >= df['lower'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1  # 将做空的信号设置为-1

    # 止盈线 x为一个小数
    df.loc[df['close'] > df['open'], 'tp_line'] = df['open'] * (1 + x)
    df.loc[df['close'] < df['open'], 'tp_line'] = df['open'] * (1 - x)

    # 合并多空信号,去除重负信号 ,不可能存在同时开多开空的信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, skipna=True, min_count=1)
    temp = df[df['signal'].notnull()][['signal']]  # 去掉空值的行,只留下有信号的
    # temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 创建一列记录有信号时候的止盈价
    condition1 = df['signal'] == 1
    condition2 = df['signal'] == -1
    t = df.loc[condition1 | condition2]

    df['tp_line2'] = t.tp_line
    df['tp_line2'].fillna(method='ffill', inplace=True)

    # 获取实际仓位
    df['pos'] = df['signal'].shift(1)  # signal信号往下挪一行才是实际仓位
    df['pos'].fillna(method='ffill', inplace=True)  # 向上补全空值(空值往上走遇到不是空值的A值,就用A值补全)
    df['pos'].fillna(value=0, inplace=True)  # 将初始行数的position补全为0

    # 平仓信号
    # 多单平仓
    condition1 = df['pos'] == 1  # 持仓为多单
    condition2 = df['close'] >= df['tp_line2']  # 收盘价到止盈价
    condition3 = df['close'] < df['median']  # 第二种平仓情况 回到中线
    condition4 = df['close'].shift(1) >= df['median'].shift(1)
    df.loc[(condition1 & condition2) | (condition3 & condition4), 'signal_long'] = 0

    # 空单平仓
    condition1 = df['pos'] == -1  # 持仓为多单
    condition2 = df['close'] <= df['tp_line2']  # 收盘价到止盈价
    condition3 = df['close'] > df['median']  # 第二种平仓情况 回到中线
    condition4 = df['close'].shift(1) <= df['median'].shift(1)
    df.loc[(condition1 & condition2) | (condition3 & condition4), 'signal_short'] = 0

    # 再写一遍
    # 合并多空信号,去除重负信号 ,不可能存在同时开多开空的信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, skipna=True, min_count=1)
    temp = df[df['signal'].notnull()][['signal']]  # 去掉空值的行,只留下有信号的
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df['pos'] = df['signal'].shift(1)  # signal信号往下挪一行才是实际仓位
    df['pos'].fillna(method='ffill', inplace=True)  # 向上补全空值(空值往上走遇到不是空值的A值,就用A值补全)
    df['pos'].fillna(value=0, inplace=True)  # 将初始行数的position补全为0

    condition1 = df['signal'] == 1
    condition2 = df['signal'] == -1
    t = df.loc[condition1 | condition2]

    df['tp_line2'] = t.tp_line

    # df['tp_line2'].fillna(method='ffill', inplace=True)

    df.drop(['median', 'upper', 'lower', 'std', 'signal_long', 'signal_short'], axis=1, inplace=True)
    # df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # print(t)
    # print(df)
    # print(df)
