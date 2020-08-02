# -*- coding: utf-8 -*-
'''检测突破信号'''
import tushare as ts
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

pro = ts.pro_api()
# 均线窗口
window_size = 5
code = '000001.SZ'

temp = ts.pro_bar(ts_code=code, adj='qfq', start_date='20200205')
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
print(results.index)
