import QUANTAXIS as QA
import pandas as pd
import datetime
import numpy as np

Account = QA.QA_Account(init_cash=10000000,allow_sellopen=True,allow_t0=True,account_cookie='futuretest',market_type=QA.MARKET_TYPE.FUTURE_CN,frequence=QA.FREQUENCE.FIFTEEN_MIN)
Broker = QA.QA_BacktestBroker()


def GetMa(dataframe,short=5,long=60):
    Time = dataframe.tradetime
    Close = dataframe.close

    LongMA = QA.MA(Close,long)
    ShortMA = QA.MA(Close,short)
    return pd.DataFrame({'datetime':Time, 'close': Close, 'shortma': ShortMA, 'longma': LongMA})

LongData = QA.QA_fetch_future_min_adv('JM1901', '2018-10-01', '2018-11-06', frequence='60min')

LongFuncData = LongData.add_func(GetMa)
#FilterLongData = LongFuncData.loc[(LongFuncData.shortma.notnull() & LongFuncData.longma.notnull())] #过滤空值
ShortData = QA.QA_fetch_future_min_adv('JM1901', '2018-10-01', '2018-11-06', frequence='1min')
ShortFuncData = ShortData.add_func(GetMa)

#通过循环跑回测
for items in LongData.panel_gen:
    _date = None
    if _date != items.date[0]:
        print('try to settle')
        _date = items.date[0]
        Account.settle()  #每天需要结算
    for item in items.security_gen:
        hr_idx = LongFuncData.loc[item.index]
        tm1 = item.index[0][0]
        tm2 = tm1+datetime.timedelta(hours=1)
        code = item.index[0][1]
        longma = 0 if np.isnan(hr_idx.longma.iloc[0]) else hr_idx.longma.iloc[0] #单个series取值
        shortma = 0 if np.isnan(hr_idx.shortma.iloc[0]) else hr_idx.shortma.iloc[0]
        if longma != 0:

            for shortitems in ShortData.selects(code,tm1,tm2).panel_gen:
                for shtitem in shortitems.security_gen:
                    shttm = shtitem.index[0][0]
                    close = shtitem.close.iloc[0]
                    print(tm1,longma,shortma,shttm,close)
                    if close <= shortma:
                        order = Account.send_order(
                            code=shtitem.index[0][1],
                            time=shttm,
                            amount=1,
                            towards=QA.ORDER_DIRECTION.BUY,
                            price=close,
                            order_model=QA.ORDER_MODEL.CLOSE,
                            amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                        )
                        event = QA.QA_Event(order=order,market_data=shtitem)
                        rec_msg = Broker.receive_order(event)
                        print(rec_msg)
                        trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                        res = trade_mes.loc[order.account_cookie, order.realorder_id]
                        order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)

                    if close  == longma:
                        print('sell')

Account.settle()
print(Account.history)
print(Account.history_table)
print(Account.daily_hold)
# Risk = QA.QA_Risk(Account,market_data=LongData,if_fq=False) #需要日线数据进行计算
Account.save()
# Risk.save()

