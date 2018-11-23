'''本策略测试移动价格法进行开平仓，在一定期间内，最低价格为起始价格下跌10%进行开仓，
可能主要使用MINMAX进行计算
'''

import QUANTAXIS as QA
import pandas as pd
import datetime
import numpy as np
import talib as ta

starttime = datetime.date(2018, 10, 16)
endtime = datetime.date(2018, 11, 10)
strstartday = str(starttime - datetime.timedelta(days=1))
strstartmaday = str(starttime - datetime.timedelta(days=90))
strstartmin = str(starttime - datetime.timedelta(days=3))
strendday = str(endtime)
strendmin = str(endtime)

init_cash = 10000000
margin = 0.1
# products = ['MA1901', 'I1901', 'RM1901', 'TA1901']
products = ['CU1901']
# products = ['TA1901', 'RB1901','RM1901']
cookie = '!'.join(products)
volume = 10  # 手数
logdic = {}

openprice = 1.24
floatrate = 0.1

tempprice = 2.2


#建立一个空的时间列表
#len temp data 取得元素的个数
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


def GetMaxMini(array,countn):
    return ta.MINMAX(array,timeperiod = countn)

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


def Buy_Open(day_product,volume,price):
    return Account.send_order(
        code=day_product.index[0][1],
        time=day_product.index[0][0],
        amount= volume,
        towards=QA.ORDER_DIRECTION.BUY_OPEN,
        price= price,
        order_model=QA.ORDER_MODEL.CLOSE,
        amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
    )


def Sell_Close(day_product,volume,price):
    return Account.send_order(
        code=day_product.index[0][1],
        time=day_product.index[0][0],
        amount=volume,
        towards=QA.ORDER_DIRECTION.SELL_CLOSE,
        price= price,
        order_model=QA.ORDER_MODEL.CLOSE,
        amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
    )

def Sell_Open(day_product,volume,price):
    return Account.send_order(
        code=day_product.index[0][1],
        time=day_product.index[0][0],
        amount=volume,
        towards=QA.ORDER_DIRECTION.SELL_OPEN,
        price=price,
        order_model=QA.ORDER_MODEL.CLOSE,
        amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
    )

def Buy_Close(day_product,volume,price):
    return Account.send_order(
        code=day_product.index[0][1],
        time=day_product.index[0][0],
        amount=volume,
        towards=QA.ORDER_DIRECTION.BUY_CLOSE,
        price=price,
        order_model=QA.ORDER_MODEL.CLOSE,
        amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
    )

def SendOrder(order,day_product,margin):
    event = QA.QA_Event(order=order, market_data=day_product)
    rec_msg = Broker.receive_order(event)
    trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
    res = trade_mes.loc[order.account_cookie, order.realorder_id]
    msg = order.trade_future(res.trade_id, res.trade_price, res.trade_amount, res.trade_time, margin)
    print(msg)

def GetPosition(Account,day_product):
    return Account.hold_available.get(day_product.index[0][1], 0)

def main(openprice):


    openprice = openprice
    DayData = QA.QA_fetch_future_day_adv(products, strstartday, strendday)
    # Day_MaData = QA.QA_fetch_future_day_adv(products, strstartmaday, strendday)
    # LongMiniData = QA.QA_fetch_future_min_adv(products, strstartmin, strendmin, frequence='60min')
    # ShortMiniData = QA.QA_fetch_future_min_adv(products, strstartmin, strendmin, frequence='1min')


    #FilterLongData = LongFuncData.loc[(LongFuncData.shortma.notnull() & LongFuncData.longma.notnull())] #过滤空值
    test_data = {}
    for pr in products:
       test_data [pr] = np.empty(0)

    #通过循环跑回测
    for day_products in DayData.panel_gen:
        _date = None
        if _date != day_products.date[0]:
            print('try to settle')
            _date = day_products.date[0]
            Account.settle()  # 每天需要结算
        for day_product in day_products.security_gen:
            # day = day_product.date[0]

            code = day_product.index[0][1]

            close = day_product.close[0]
            if len(test_data[code])>1:
                max,min = GetMaxMini(test_data[code],len(test_data[code]))
                if abs(max[-1]/openprice-1)>= floatrate:
                    print(max[-1])
                    position = GetPosition(Account,day_product)
                    if abs(position)!=0:
                       order = Sell_Close(day_product,volume,close)
                       print(order)
                       SendOrder(order,day_product,margin)
                    else:
                        order = Sell_Open(day_product,volume,close)
                        print(order)
                        test_data[code]=np.empty(0)
                        # test_data[code]=np.append(test_data,close)
                        openprice = close
                if abs(max[-1]/openprice-1)>= floatrate:
                    print(max[-1])
                    position = GetPosition(Account, day_product)
                    if abs(position) != 0:
                        order = Buy_Close(day_product, volume, close)
                        print(order)
                        SendOrder(order,day_product,margin)
                    else:
                        order = Buy_Open(day_product, volume, close)
                        print(order)
                        SendOrder(order,day_product,volume)
                        test_data[code] = np.empty(0)
                        # test_data[code] = np.append(test_data[code], close)
                        openprice = close
            if len(test_data[code])<2:
                order = Buy_Open(day_product,volume,close)
                print(order)
                SendOrder(order,day_product,margin)

            test_data[code] = np.append(test_data[code],close)
    Account.settle()
    #print(Account.history)
    print(Account.history_table)
    print(Account.daily_hold)
    Risk = QA.QA_Risk(Account,market_data=DayData,if_fq=False) #需要日线数据进行计算
    Account.save()
    Account.daily_hold.to_csv('hold_daily.csv')
    Account.history_table.to_csv('history_table.csv')
    Account.trade.to_csv('trademx.csv')

    Risk.assets.to_csv('asserts.csv')

    plt=Risk.plot_future_assets_curve()

    plt.show()

if __name__ == '__main__':
    main(1000)
