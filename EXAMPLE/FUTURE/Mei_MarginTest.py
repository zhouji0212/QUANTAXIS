import QUANTAXIS as QA
import pandas as pd
import datetime
import numpy as np

starttime = datetime.date(2018,1,16)
endtime = datetime.date(2018,11,10)
strstartday = str(starttime-datetime.timedelta(days=1))
strstartmaday = str(starttime-datetime.timedelta(days=90))
strstartmin = str(starttime-datetime.timedelta(days=3))
strendday = str(endtime)
strendmin = str(endtime)

init_cash = 10000
margin = 1
#products = ['MA1901', 'I1901', 'RM1901', 'TA1901']
products = ['RBL8']
#products = ['TA1901', 'RB1901','RM1901']
cookie = '!'.join(products)
volume = 1 #手数
logdic = {}

#JM1901
#I1901
#RM1901
#MA1901
#TA1901
#3个一起跑下

Account = QA.QA_Account(init_cash=init_cash,allow_sellopen=True, allow_t0=True,
                        account_cookie=cookie,market_type=QA.MARKET_TYPE.FUTURE_CN,
                         frequence=QA.FREQUENCE.FIFTEEN_MIN)
Broker = QA.QA_BacktestBroker()


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

DayData = QA.QA_fetch_future_day_adv(products, strstartday, strendday)
Day_MaData = QA.QA_fetch_future_day_adv(products, strstartmaday, strendday)
LongMiniData = QA.QA_fetch_future_min_adv(products, strstartmin, strendmin, frequence='60min')
ShortMiniData = QA.QA_fetch_future_min_adv(products, strstartmin, strendmin, frequence='1min')

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
        day = day_product.date[0]
        close = day_idx.close.iloc[0]

        day_ma20 = 0 if np.isnan(day_idx.longma.iloc[0]) else day_idx.longma.iloc[0]
        day_ma5 = day_idx.shortma.iloc[0]
        logdic['date','close','dma20','dma5']=day,close,day_ma20,day_ma5
        # if Account.hold_available.empty :
        #     pass
        #均线指标上穿，做多
        if day_ma20!=0 and day_ma5 >=day_ma20:
            position = Account.hold_available.get(day_product.index[0][1], 0)
            if position<0:
                #先买入平仓再开仓
                order = Account.send_order(
                    code=day_product.index[0][1],
                    time=day_product.index[0][0],
                    towards=QA.ORDER_DIRECTION.BUY_CLOSE,
                    price=close*margin,
                    order_model=QA.ORDER_MODEL.CLOSE,
                    amount_model=QA.AMOUNT_MODEL.BY_AMOUNT,
                    amount= abs(Account.hold_available.get(day_product.index[0][1])))
                event = QA.QA_Event(order=order, market_data=day_product)
                rec_msg = Broker.receive_order(event)
                trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                res = trade_mes.loc[order.account_cookie, order.realorder_id]
                msg = order.trade(res.trade_id, res.trade_price*margin, res.trade_amount, res.trade_time)
                print(msg)
                #先平仓后再开仓
                order = Account.send_order(
                    code=day_product.index[0][1],
                    time=day_product.index[0][0],
                    amount=volume,
                    towards=QA.ORDER_DIRECTION.BUY_OPEN,
                    price=close * margin,
                    order_model=QA.ORDER_MODEL.CLOSE,
                    amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                )
                event = QA.QA_Event(order=order, market_data=day_product)
                rec_msg = Broker.receive_order(event)
                trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                res = trade_mes.loc[order.account_cookie, order.realorder_id]
                msg = order.trade(res.trade_id, res.trade_price * margin, res.trade_amount, res.trade_time)
                print(msg)
                position = volume
           #开仓 多单
            elif position==0:
                order = Account.send_order(
                    code=day_product.index[0][1],
                    time=day_product.index[0][0],
                    amount=volume,
                    towards=QA.ORDER_DIRECTION.BUY_OPEN,
                    price=close*margin,
                    order_model=QA.ORDER_MODEL.CLOSE,
                    amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                )
                event = QA.QA_Event(order=order, market_data=day_product)
                rec_msg = Broker.receive_order(event)
                trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                res = trade_mes.loc[order.account_cookie, order.realorder_id]
                msg = order.trade(res.trade_id, res.trade_price*margin, res.trade_amount, res.trade_time)
                print(msg)
            elif abs(position) == volume:
                print('不动')
        #均线指标下穿 做空
        if day_ma5<=day_ma20:
            # if Account.hold_available.empty:
            #     pass
            #
            position = Account.hold_available.get(day_product.index[0][1], 0)
            if position > 0:  #有多仓先平仓
                order =Account.send_order(
                    code=day_product.index[0][1],
                    time=day_product.index[0][0],
                    towards=QA.ORDER_DIRECTION.SELL_CLOSE,
                    price=close*margin,
                    order_model=QA.ORDER_MODEL.CLOSE,
                    amount_model=QA.AMOUNT_MODEL.BY_AMOUNT,
                    amount= abs(Account.hold_available.get_values()[0])
                )
                event = QA.QA_Event(order=order, market_data=day_product)
                rec_msg = Broker.receive_order(event)
                # print(rec_msg)
                trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                res = trade_mes.loc[order.account_cookie, order.realorder_id]  #这个地方要修正下保证金参数
                msg = order.trade(res.trade_id, res.trade_price*margin, res.trade_amount, res.trade_time)
                print(msg)
                order = Account.send_order(
                    code=day_product.index[0][1],
                    time=day_product.index[0][0],
                    amount=abs(volume),
                    towards=QA.ORDER_DIRECTION.SELL_OPEN,
                    price=close * margin,
                    order_model=QA.ORDER_MODEL.CLOSE,
                    amount_model=QA.AMOUNT_MODEL.BY_AMOUNT

                )
                event = QA.QA_Event(order=order, market_data=day_product)
                rec_msg = Broker.receive_order(event)
                # print(rec_msg)
                trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                res = trade_mes.loc[order.account_cookie, order.realorder_id]
                msg = order.trade(res.trade_id, res.trade_price * margin, res.trade_amount, res.trade_time)
                print(msg)
                position = volume

            elif position==0:
                order = Account.send_order(
                    code=day_product.index[0][1],
                    time=day_product.index[0][0],
                    amount=volume,
                    towards=QA.ORDER_DIRECTION.SELL_OPEN,
                    price=close*margin,
                    order_model=QA.ORDER_MODEL.CLOSE,
                    amount_model=QA.AMOUNT_MODEL.BY_AMOUNT

                )
                event = QA.QA_Event(order=order, market_data=day_product)
                rec_msg = Broker.receive_order(event)
                #print(rec_msg)
                trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                res = trade_mes.loc[order.account_cookie, order.realorder_id]
                msg = order.trade(res.trade_id, res.trade_price* margin, res.trade_amount, res.trade_time)
                print(msg)
            elif abs(position) == volume:
                print('不用动仓位')
Account.settle()
#print(Account.history)
print(Day_idx)
print(Account.history_table)
print(Account.daily_hold)
Risk = QA.QA_Risk(Account,market_data=DayData,if_fq=False) #需要日线数据进行计算
Account.save()
Account.daily_hold.to_csv('hold_daily.csv')
Account.history_table.to_csv('history_table.csv')
Account.trade.to_csv('trademx.csv')

Risk.assets.to_csv('asserts.csv')

plt=Risk.plot_assets_curve()

plt.show()