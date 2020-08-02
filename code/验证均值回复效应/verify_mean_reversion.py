# -*- coding: utf-8 -*-
import tushare as ts
import matplotlib.pyplot as plt
import pandas as pd

pro = ts.pro_api()

start_date = '20180501'
end_date = '20200531'
obs_percent = 0.3
cmp_percent = 0.1

# 查询当前所有正常上市交易的股票列表
stock_list = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
stock_list = stock_list.set_index('ts_code')['name']

pf_list = []
count = 0
# 对series每一行进行迭代
for code, name in stock_list.iteritems():
    # 如果能找到ST就跳过，找不到就返回-1
    if name.find('ST') != -1:
        continue
    df = ts.pro_bar(ts_code=code, adj='qfq', start_date=start_date, end_date=end_date)
    if len(df) < 400:
        continue
    df.index = df.pop('trade_date')
    df.sort_index(ascending=True, inplace=True)
    win_size = int(len(df) * obs_percent)

    # 第一段时间收益率
    profit_1 = int((df['close'][win_size - 1] / df['close'][0] - 1.0) * 100)
    # 第二段时间收益率
    profit_2 = int((df['close'][-1] / df['close'][-win_size] - 1.0) * 100)
    if profit_1 > 150 or profit_2 > 150:
        continue
    pf_list.append(dict(code=code, pf1=profit_1, pf2=profit_2))

    count += 1
    print(count)
    if count > 100:
        break

# step1
pf_list.sort(key=lambda x: x['pf1'], reverse=True)
# 给排好序的列表增加排名
for idx, doc in enumerate(pf_list):
    doc["rank_1"] = idx

num_cands = int(len(pf_list) * cmp_percent)  # 取前后10%
top_cands = pf_list[:num_cands]  # 组合1,时间段1涨的最好的
btm_cands = pf_list[-num_cands:]  # 组合2，时间段1涨的最差的
top_group_codes = set([doc['code'] for doc in top_cands])  # 组合1的代码集合
btm_group_codes = set([doc['code'] for doc in btm_cands])  # 组合2的代码集合
# 组合1的平均排名
avg_top_idx = round(sum([doc['rank_1'] for doc in top_cands]) / num_cands / len(pf_list), 2)
# 组合2的平均排名
avg_btm_idx = round(sum([doc['rank_1'] for doc in btm_cands]) / num_cands / len(pf_list), 2)
avg_mid_idx = (0 + len(pf_list) - 1) / 2 / len(pf_list)  # ==0.5

# step2
pf_list.sort(key=lambda x: x['pf2'], reverse=True)
# 给排好序的列表增加排名
for idx, doc in enumerate(pf_list):
    doc["rank_2"] = idx

# 组合1的平均排名
cmp_avg_top_idx = round(
    sum([doc['rank_2'] for doc in pf_list if doc['code'] in top_group_codes]) / num_cands / len(pf_list), 2)
# 组合2的平均排名
cmp_avg_btm_idx = round(
    sum([doc['rank_2'] for doc in pf_list if doc['code'] in btm_group_codes]) / num_cands / len(pf_list), 2)

print("Top group :", avg_top_idx, "-->", cmp_avg_top_idx, "(avg: %.2f)" % avg_mid_idx)
print("Btm group :", avg_btm_idx, "-->", cmp_avg_btm_idx, "(avg: %.2f)" % avg_mid_idx)

# 所有股票在时间段1和时间段2的收益
profits = pd.DataFrame({"pf1": [doc["pf1"] for doc in pf_list],
                        "pf2": [doc["pf2"] for doc in pf_list]})

profits.plot.hist(bins=200, alpha=0.5)
plt.show()
