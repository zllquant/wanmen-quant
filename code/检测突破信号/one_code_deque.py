# -*- coding: utf-8 -*-
'''检测突破信号'''
import tushare as ts
import pandas as pd
from collections import deque


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
# 队列
observe_win = deque(maxlen=window_size)

pre_bo = False
for bar in bars:
    if len(observe_win) == window_size:
        hhv = max([doc['high'] for doc in observe_win])
        # break_out 信号
        cur_bo = False
        # 突破高点
        if bar['close'] > hhv:
            cur_bo = True
        # 今日突破,昨日未突破
        if cur_bo and not pre_bo:
            print(bar['date'])
        # 记录上一个循环的突破信号,不用重复计算
        pre_bo = cur_bo
    observe_win.append(bar)




