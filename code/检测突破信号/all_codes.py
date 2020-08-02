# -*- coding: utf-8 -*-
'''检测突破信号'''
import tushare as ts
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

pro = ts.pro_api()
# 均线窗口
window_size = 55
all_stocks = pro.stock_basic(exchange='', list_status='L', fields='ts_code,name')
all_stocks = all_stocks.set_index('ts_code')['name']

for code, name in all_stocks.iteritems():
    temp = ts.pro_bar(ts_code=code, adj='qfq', start_date='20200205')
    # 先判断不为空,可能这段日期是停牌的
    if len(temp) == 0:
        continue
    if name.find('ST') != -1:
        continue
    temp.index = temp.pop('trade_date')
    temp.sort_index(ascending=True, inplace=True)

    df = temp.loc[:, ['high', 'close']]
    # 上轨
    df['hhv'] = df['high'].rolling(window_size).max()
    df['pre_hhv'] = df['hhv'].shift(1)

    # 今天的收盘价站上了昨日前n日高点
    # 昨天的收盘价没有冲破前一天n日的高点
    df['signal'] = (df['close'] > df['pre_hhv']) & \
                   (df['close'].shift(1) <= df['pre_hhv'].shift(1))

    results = df[df['signal']]
    if len(results) > 0:
        print(code, name, list(results.index))
