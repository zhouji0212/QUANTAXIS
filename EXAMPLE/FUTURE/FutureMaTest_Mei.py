import QUANTAXIS as QA
import pandas as pd
import datetime
import numpy as np
import QA_HFReport.report_stra
from QA_HFReport.bar import Bar
listbar = []
starttime = datetime.date(2018,4,26)
endtime = datetime.date(2018,11,10)
strstartday = str(starttime-datetime.timedelta(days=1))
strstartmaday = str(starttime-datetime.timedelta(days=90))
strstartmin = str(starttime-datetime.timedelta(days=3))
strendday = str(endtime)
strendmin = str(endtime)


product = 'JM1901'

Account = QA.QA_Account(init_cash=10000000,allow_sellopen=True,allow_t0=True,account_cookie='futuretest',market_type=QA.MARKET_TYPE.FUTURE_CN,frequence=QA.FREQUENCE.FIFTEEN_MIN)
Broker = QA.QA_BacktestBroker()


def GetGenBarList(dataframe):
    '''制造bar数据'''
    bar = Bar(str(dataframe.index[0][0]),
              dataframe.index[0][1],
              tradingday=dataframe.index[0][0],
              h=dataframe.high[0],
              l=dataframe.low[0],
              o = dataframe.open[0],
              c = dataframe.close[0],
              i = dataframe.close[0]
              )
    listbar.append(bar)




def GetMaDay(dataframe,short=5,long=20):

    Close = dataframe.close

    LongMA = QA.MA(Close,long)
    ShortMA = QA.MA(Close,short)
    return pd.DataFrame({'close': Close, 'shortma': ShortMA, 'longma': LongMA})

def GetMa(dataframe,short=5,long=60):
    tradetime = dataframe.tradetime
    close = dataframe.close

    LongMA = QA.MA(close,long)
    ShortMA = QA.MA(close,short)
    return pd.DataFrame({'tradetime':tradetime, 'close': close, 'shortma': ShortMA, 'longma': LongMA})

DayData = QA.QA_fetch_future_day_adv(product,strstartday,strendday)
Day_MaData = QA.QA_fetch_future_day_adv(product,strstartmaday,strendday)
LongMiniData = QA.QA_fetch_future_min_adv(product, strstartmin, strendmin, frequence='60min')
ShortMiniData = QA.QA_fetch_future_min_adv(product, strstartmin, strendmin, frequence='1min')
Day_idx = Day_MaData.add_func(GetMaDay)
Long_idx = LongMiniData.add_func(GetMa)
#FilterLongData = LongFuncData.loc[(LongFuncData.shortma.notnull() & LongFuncData.longma.notnull())] #过滤空值



#通过循环跑回测
for day_products in DayData.panel_gen:
    _date = None
    if _date != day_products.date[0]:
        print('try to settle')
        _date = day_products.date[0]
        Account.settle()  # 每天需要结算
    for day_product in day_products.security_gen:
        day_idx = Day_idx.loc[day_product.index]
        ma60_day = 0 if np.isnan(day_idx.longma.iloc[0]) else day_idx.longma.iloc[0] #过滤空值
        day = day_product.date[0]
        close = day_idx.close.iloc[0]
        if ma60_day!=0:
            for items in LongMiniData.selects(product, day, day).security_gen: #选择日期
                for item in items.security_gen:
                    hr_idx = Long_idx.loc[item.index]
                    tm1 = item.index[0][0]
                    tm2 = tm1+datetime.timedelta(hours=1)
                    code = item.index[0][1]
                    ma60_hour = 0 if np.isnan(hr_idx.longma.iloc[0]) else hr_idx.longma.iloc[0] #取得小时均线
                    for testitems in ShortMiniData.selects(code, tm1, tm2).panel_gen:
                        for testitem in testitems.security_gen:
                            shttm = testitem.index[0][0]
                            close = testitem.close.iloc[0]
                            print(tm1, ma60_hour, shttm, close)
                            if close >= ma60_hour and close>=ma60_day:
                                order = Account.send_order(
                                    code=testitem.index[0][1],
                                    time=shttm,
                                    amount=1,
                                    towards=QA.ORDER_DIRECTION.BUY,
                                    price=close,
                                    order_model=QA.ORDER_MODEL.CLOSE,
                                    amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                                )
                                event = QA.QA_Event(order=order, market_data=testitem)
                                rec_msg = Broker.receive_order(event)
                                #print(rec_msg)
                                trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                                res = trade_mes.loc[order.account_cookie, order.realorder_id]
                                order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)

                                if close <= ma60_hour and close <= ma60_day:
                                    order = Account.send_order(
                                        code=testitem.index[0][1],
                                        time=shttm,
                                        amount=1,
                                        towards=QA.ORDER_DIRECTION.SELL,
                                        price=close,
                                        order_model=QA.ORDER_MODEL.CLOSE,
                                        amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                                    )
                                    event = QA.QA_Event(order=order, market_data=testitem)
                                    rec_msg = Broker.receive_order(event)
                                    #print(rec_msg)
                                    trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                                    res = trade_mes.loc[order.account_cookie, order.realorder_id]
                                    order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)

Account.settle()
print(Account.history)
print(Account.history_table)
print(Account.daily_hold)
Risk = QA.QA_Risk(Account,market_data=DayData,if_fq=False) #需要日线数据进行计算

Account.save()
Risk.save()

