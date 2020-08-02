# -*- coding: utf-8 -*-
import pymongo
from pymongo import MongoClient
import matplotlib.pyplot as plt
import matplotlib.dates as mdate
from datetime import datetime
import pandas as pd

db = MongoClient(host='localhost', port=27017)['my_quant']
initial_capital = 10000000
base_code = '000300.SH'


def calc_holding_value(account_id):
    """
    计算持仓股总市值
    :param account_id: 账户ID
    :return:
    """
    # 持仓股总市值
    holding_value = 0
    # 查某个账户的所有持仓信息
    holding_stock_cursor = db.holding_stock.find({'account_id': account_id})
    for holding_stock in holding_stock_cursor:
        # 股票代码
        code = holding_stock['code']
        # 持仓量
        volume = holding_stock['volume']
        # 取出某天的日线数据
        daily = db.daily.find_one({'code': code, 'time': '20200202'})
        close = daily['close']
        # 持仓市值 = 收盘价 * 持仓股数
        value = close * volume
        # 所有持仓股票市值加和
        holding_value += value

    return holding_value


def calc_capital(account_id):
    """
    计算总资产
    :param account_id:
    :return:
    """
    # 账户
    account = db.account.find_one({'account_id': account_id})
    # 可用现金
    cash = account['cash']
    print('cash:%s' % cash)
    # 持仓股总市值
    holding_value = calc_holding_value(account_id)
    # 总资金
    capital = holding_value + cash
    print("capital:%s" % capital)

    return capital


def calc_net_value(account_id):
    """
    计算净值
    :param account_id:
    :return:
    """
    capital = calc_capital(account_id)
    net_value = capital / initial_capital
    print("net_value:%s" % net_value)
    return net_value


def calc_daily_profit(account_id):
    """
    计算每日收益(累计)
    :param account_id:
    :return:
    """
    net_value = calc_net_value(1)
    profit = round((net_value - 1) * 100, 2)
    print("profit:%s" % profit)


def draw_profit_chart(account_id):
    """
    画累计收益曲线
    :param account_id:
    :return:
    """
    dates = []
    profits = []
    account_history_cursor = db.account_history.find({"account_id": account_id},
                                                     sort=[('date', pymongo.ASCENDING)])
    for account_history in account_history_cursor:
        # 取出当天日期
        date = account_history['date']
        dates.append(datetime.strptime(date, "%Y-%m-%d").date())
        # 当日总资金
        capital = account_history['capital']
        # 计算当日累计收益
        profit = (capital - initial_capital) / initial_capital * 100
        profits.append(profit)

    fig = plt.figure(figsize=(12, 6))
    ax1 = fig.add_subplot(1, 1, 1)
    # 打开网格
    ax1.yaxis.grid(color='black', ls='--', lw=1, alpha=0.2)
    # 设置收益曲线
    ax1.plot(dates, profits, color='blue', ls='-', lw=1, alpha=0.5)
    # 设置ax1区域背景颜色
    ax1.patch.set_facecolor("gray")
    # 设置ax1区域背景颜色透明度
    ax1.patch.set_alpha(0.2)
    # 设置时间显示格式
    ax1.xaxis.set_major_formatter(mdate.DateFormatter("%Y-%m-%d"))
    plt.show()


def calc_simple_annual_profit(account_id):
    capitals = []
    account_history_cursor = db.account_history.find({"account_id": account_id},
                                                     sort=[('date', pymongo.ASCENDING)])
    for account_history in account_history_cursor:
        capital = account_history['capital']
        capitals.append(capital)

    # 当前总资产
    current_capital = capitals[-1]
    # 累计收益 = (当前总资产-初始资产)/初始资产
    current_profit = (current_capital / initial_capital - 1) * 100
    # 交易日数
    trading_days = len(capitals)
    # 单利年化 = 累计收益/投资年限
    simple_annual_profit = current_profit / trading_days * 250
    print('simple_annual_profit:%s' % simple_annual_profit)

    return simple_annual_profit


def calc_compound_annual_profit(account_id):
    capitals = []
    account_history_cursor = db.account_history.find({"account_id": account_id},
                                                     sort=[('date', pymongo.ASCENDING)])
    for account_history in account_history_cursor:
        capital = account_history['capital']
        capitals.append(capital)

    # 当前总资产
    current_capital = capitals[-1]
    # 净值 = 期末/期初
    net_value = current_capital / initial_capital
    trading_days = len(capitals)
    # 投资年限
    years = trading_days / 250
    # 复利年化 = (期末/期初) ** (1/years) - 1
    compound_annual_profit = (pow(net_value, 1 / years) - 1) * 100

    return compound_annual_profit


def calc_sharpe(account_id):
    account_history_cursor = db.account_history.find({"account_id": account_id},
                                                     sort=[('date', pymongo.ASCENDING)])
    # 月收益率
    profits = []
    # 月收益率求和
    total_profit = 0
    # 上一个月的资产
    last_capital = 0
    index = 0
    for account_history in account_history_cursor:
        # 取出每天的总资产
        capital = account_history['capital']
        if index == 0:
            last_capital = capital
            index += 1
            continue
        if index % 22 == 0:
            # 月收益
            profit = (capital - last_capital) / last_capital * 100
            profits.append(profit)
            # 月收益累加
            total_profit = total_profit + profit
            last_capital = capital
        index += 1

    # 月收益的均值
    profit_mean = total_profit / len(profits)
    total_diff_pow = 0
    for profit in profits:
        total_diff_pow = total_diff_pow + pow(profit - profit_mean, 2)
    # 月收益的标准差
    profit_std = pow(total_diff_pow / len(profits), 0.5)
    # 夏普 = (简单年化收益- 无风险) / 年化标准差
    sharpe = (profit_mean * 12 - 1.5) / (profit_std * pow(12, 0.5))
    print('sharpe:%s' % sharpe)

    return sharpe


def calc_max_drawdown(account_id):
    account_history_cursor = db.account_history.find({"account_id": account_id},
                                                     sort=[('date', pymongo.ASCENDING)])
    capitals = [account_history['capital'] for account_history in account_history_cursor]

    # 最大回撤
    max_drawdown = 0
    # 之前资产最高点
    max_capital = 0
    for capital in capitals:
        if capital > max_capital:
            max_capital = capital
        # 计算当天回撤
        drawdown = 1 - capital / max_capital
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return max_drawdown


def calc_alpha(account_id):
    account_history_cursor = db.account_history.find({"account_id": account_id},
                                                     sort=[('date', pymongo.ASCENDING)])
    df = pd.DataFrame(columns=['profit', 'base_profit'])

    last_capital = 0
    last_base_close = 0

    index = 0
    df_index = 0

    for account_history in account_history_cursor:
        # 这天日期
        date = account_history['date']
        # 这天总资金
        capital = account_history['capital']
        if index == 0:
            last_capital = capital
            daily = db.daily.find_one({'code': base_code, 'time': date},
                                      projection={'close': True})
            # 基准的收盘价
            last_base_close = daily['close']
            index += 1
            continue

        if index % 22 == 0:
            # 月收益
            profit = (capital - last_capital) / last_capital * 100
            daily = db.daily.find_one({'code': base_code, 'time': date},
                                      projection={'close': True})
            base_close = daily['close']
            # 基准的月收益
            base_profit = (base_close - last_base_close) / last_base_close * 100
            df.loc[df_index] = {'profit': profit, 'base_profit': base_profit}
            last_base_close = base_close
            df_index += 1
        index += 1

    # 计算beta ,利用公式
    cov = df['profit'].cov(df['base_profit'])
    # 计算基准的方差
    base_var = df['base_profit'].var()
    beta = cov / base_var

    # 再算alpha
    profit_mean = df['profit'].mean()
    base_profit_mean = df['base_profit'].mean()
    # 这里算的是12个月累计的alpha
    alpha = profit_mean * 12 - 1.5 - beta * (base_profit_mean * 12 - 1.5)

    # 年化残差风险 omega
    profit_var = df['profit'].var()
    omega = pow((profit_var - pow(beta, 2) * base_var) * 12, 1 / 2)
    ir = alpha / omega

    return alpha, beta, ir
