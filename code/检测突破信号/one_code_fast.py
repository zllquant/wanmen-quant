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

# 换一种数据结构速度会快很多
bars = [{'date': row.Index, 'high': row.high, 'close': row.close} for row in df.itertuples()]

pre_bo = False
for start in range(len(bars)):
    # 滑动窗口
    end = start + window_size
    if end >= len(bars):
        break
    # 切出观察窗口
    observe_win = bars[start:end]
    # 求出窗口内最高点
    hhv = max([bar['high'] for bar in observe_win])
    # 判断下一日的收盘是否大于前n日上轨
    next_bar = bars[end]

    # break_out 信号
    cur_bo = False
    # 突破高点
    if next_bar['close'] > hhv:
        cur_bo = True
    # 今日突破,昨日未突破
    if cur_bo and not pre_bo:
        print(next_bar['date'])
    # 记录上一个循环的突破信号,不用重复计算
    pre_bo = cur_bo
