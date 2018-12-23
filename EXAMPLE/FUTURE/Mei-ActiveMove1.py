'''本策略测试移动价格法进行开平仓，在一定期间内，最低价格为起始价格下跌10%进行开仓，
可能主要使用MINMAX进行计算
'''

import QUANTAXIS as QA
import pandas as pd
import datetime
import numpy as np
import talib as ta

class Test_ActiveMove():

    def __init__(self):
        self.starttime = datetime.date(2018, 1, 1)
        self.endtime = datetime.date(2018, 12,21 )
        self.strstartday = str(self.starttime - datetime.timedelta(days=1))
        self.strstartmaday = str(self.starttime - datetime.timedelta(days=90))
        self.strstartmin = str(self.starttime - datetime.timedelta(days=3))
        self.strendday = str(self.endtime)
        self.strendmin = str(self.endtime)

        self.init_cash = 200000
        self.margin = 0.1
        # products = ['MA1901', 'I1901', 'RM1901', 'TA1901']
        self.products = ['TA1901']
        # products = ['TA1901', 'RB1901','RM1901']
        self.cookie = '!'.join(self.products)
        self.volume = 10  # 手数
        self.logdic = {}

        self.openprice = 1.24
        self.floatrate = 0.05

        self.tempprice = 2.2
        self.buy_position = {}
        self.sell_position = {}
        self.code = None
        self.temp_close = 0.00
        self.temp_dayproduct = {}
        self.Account = QA.QA_Account(init_cash=self.init_cash, allow_sellopen=True, allow_t0=True,
                                market_type=QA.MARKET_TYPE.FUTURE_CN,
                                frequence=QA.FREQUENCE.DAY,margin_rate=self.margin)
        self.Broker = QA.QA_BacktestBroker()

#建立一个空的时间列表
#len temp data 取得元素的个数
#JM1901
#I1901
#RM1901
#MA1901
#TA1901
#3个一起跑下




    def GetMaxMini(self,array,countn):
        return ta.MINMAX(array,timeperiod = countn)

    def GetMaDay(self,dataframe,short=5,long=20):

        Close = dataframe.close

        LongMA = QA.MA(Close,long)
        ShortMA = QA.MA(Close,short)
        return pd.DataFrame({'close': Close, 'shortma': ShortMA, 'longma': LongMA})

    def GetMa(self,dataframe,short=5,long=60):
        tradetime = dataframe.tradetime
        close = dataframe.close

        LongMA = QA.MA(close,long)
        ShortMA = QA.MA(close,short)
        return pd.DataFrame({'tradetime':tradetime, 'close': close, 'shortma': ShortMA, 'longma': LongMA})


    def Buy_Open(self,day_product,volume,price):
        return self.Account.send_order(
            code=day_product.index[0][1],
            time=day_product.index[0][0],
            amount= volume,
            towards=QA.ORDER_DIRECTION.BUY_OPEN,
            price= price,
            order_model=QA.ORDER_MODEL.CLOSE,
            amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
        )


    def Sell_Close(self,day_product,volume,price):
        return self.Account.send_order(
            code=day_product.index[0][1],
            time=day_product.index[0][0],
            amount=volume,
            towards=QA.ORDER_DIRECTION.SELL_CLOSE,
            price= price,
            order_model=QA.ORDER_MODEL.CLOSE,
            amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
        )

    def Sell_Open(self,day_product,volume,price):
        return self.Account.send_order(
            code=day_product.index[0][1],
            time=day_product.index[0][0],
            amount=volume,
            towards=QA.ORDER_DIRECTION.SELL_OPEN,
            price=price,
            order_model=QA.ORDER_MODEL.CLOSE,
            amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
        )

    def Buy_Close(self,day_product,volume,price):
        return self.Account.send_order(
            code=day_product.index[0][1],
            time=day_product.index[0][0],
            amount=volume,
            towards=QA.ORDER_DIRECTION.BUY_CLOSE,
            price=price,
            order_model=QA.ORDER_MODEL.CLOSE,
            amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
        )

    def SendOrder(self,order,day_product):
        event = QA.QA_Event(order=order, market_data=day_product)
        rec_msg = self.Broker.receive_order(event)
        trade_mes = self.Broker.query_orders(self.Account.account_cookie,'filled')
        res = trade_mes.iloc[-1]
        msg = order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)
        print('sendorder',res)

    def GetPosition(self,Account,day_product):
        return self.Account.hold_available.get(day_product.index[0][1], 0)

    def main(self,openprice):


        openprice = openprice
        DayData = QA.QA_fetch_future_day_adv(self.products, self.strstartday, self.strendday)
        # Day_MaData = QA.QA_fetch_future_day_adv(products, strstartmaday, strendday)
        # LongMiniData = QA.QA_fetch_future_min_adv(products, strstartmin, strendmin, frequence='60min')
        # ShortMiniData = QA.QA_fetch_future_min_adv(products, strstartmin, strendmin, frequence='1min')


        #FilterLongData = LongFuncData.loc[(LongFuncData.shortma.notnull() & LongFuncData.longma.notnull())] #过滤空值
        test_data = {}
        for pr in self.products:
           test_data [pr] = np.empty(0)

        #通过循环跑回测
        _date = None
        for day_products in DayData.panel_gen:

            if _date != day_products.date[0]:

                _date = day_products.date[0]
                print(str(_date), 'try to settle')
                self.Account.settle()  # 每天需要结算
            for day_product in day_products.security_gen:
                # day = day_product.date[0]

                code = day_product.index[0][1]

                close = day_product.close[0]
                self.temp_dayproduct[code] = day_product
                self.temp_close = close
                self.code = code
                if len(test_data[code])>1:
                    min,max = self.GetMaxMini(test_data[code],len(test_data[code]))
                    buy_position = self.Account.future_hold_detail[code][QA.ORDER_DIRECTION.BUY_OPEN]
                    sell_position = self.Account.future_hold_detail[code][QA.ORDER_DIRECTION.SELL_OPEN]
                    self.buy_position[code] = buy_position
                    self.sell_position[code] = sell_position
                    print('mini、max、Open、lowrate、highrate ：',min[-1],max[-1], openprice, min[-1]/openprice-1,max[-1]/openprice-1)
                    if (max[-1] / close - 1) >= self.floatrate :
                        print('mini:',min[-1],-(min[-1]/openprice-1))
                    #position = GetPosition(Account,day_product)
                        if abs(buy_position) > 0 :
                            order = self.Sell_Close(day_product,self.volume,close)
                            print(order)
                            self.SendOrder(order,day_product)
                            order = self.Sell_Open(day_product, self.volume, close)
                            print(order)
                            self.SendOrder(order,day_product)
                            test_data[code] = np.empty(0)
                            openprice = close
                            test_data[code] = np.append(test_data[code], close)
                            test_data[code] = np.append(test_data[code], close)
                            self.sell_position[code] = self.Account.future_hold_detail[code][-2]
                           #
                        # elif abs(sell_position) == 0:
                        #     order = Sell_Open(day_product,volume,close)
                        #     print(order)
                        #     SendOrder(order,day_product)
                        #     test_data[code]=np.empty(0)
                        #     test_data[code]=np.append(test_data[code],close)
                        #     test_data[code] = np.append(test_data[code], close)
                        #     openprice = close
                    if -(min[-1]/close-1)>= self.floatrate and (max[-1]/openprice-1)!=0.0 :
                        print('max:',max[-1],max[-1]/openprice-1)
                        # position = GetPosition(Account, day_product)
                        if sell_position > 0 :
                            order = self.Buy_Close(day_product, self.volume, close)
                            print(order)
                            self.SendOrder(order,day_product)
                            order = self.Buy_Open(day_product, self.volume, close)
                            print(order)
                            self.SendOrder(order, day_product)
                            test_data[code] = np.empty(0)
                            test_data[code] = np.append(test_data[code], close)
                            test_data[code] = np.append(test_data[code], close)
                        # test_data[code] = np.append(test_data[code], close)
                            openprice = close
                            self.buy_position[code] = self.Account.future_hold_detail[code][2]
                        # elif sell_position == 0:
                        #     order = Buy_Open(day_product, volume, close)
                        #     print(order)
                        #     SendOrder(order,day_product)
                        #     test_data[code] = np.empty(0)
                        #     test_data[code] = np.append(test_data[code], close)
                        #     test_data[code] = np.append(test_data[code], close)
                        #     # test_data[code] = np.append(test_data[code], close)
                        #     openprice = close
                if len(test_data[code])<1:
                    order = self.Buy_Open(day_product,self.volume,close)
                    print(order)
                    self.SendOrder(order,day_product)
                    openprice = close
                    test_data[code] = np.append(test_data[code], close)
                    test_data[code] = np.append(test_data[code], close)

                test_data[code] = np.append(test_data[code],close)


                print(self.Account.future_hold_detail)


            self.Account.settle() #ri
        print(self.temp_close)
        print(self.temp_dayproduct[code].data)
        for code in self.Account.future_hold_detail.keys():
            if self.Account.future_hold_detail[code][QA.ORDER_DIRECTION.BUY_OPEN] != 0 :
                order = self.Sell_Close(self.temp_dayproduct[code],self.volume,self.temp_close)
                self.SendOrder(order,self.temp_dayproduct[code])
                self.Account.settle()
            if self.Account.future_hold_detail[code][QA.ORDER_DIRECTION.SELL_OPEN] != 0:
                order = self.Buy_Close(self.temp_dayproduct[code],self.volume,self.temp_close)
                self.SendOrder(order,self.temp_dayproduct[code])
                self.Account.settle()

        #print(Account.history)
        print(self.Account.future_hold_detail)
        print(self.Account.history_table)
        print(self.Account.daily_hold)

        self.Account.save()
        # self.Account.daily_hold.to_csv('hold_daily.csv')
        self.Account.history_table.to_clipboard()
        # self.Account.trade.to_csv('trademx.csv')
        Risk = QA.QA_Risk(self.Account, market_data=DayData, if_fq=False, market_type='future')  # 需要日线数据进行计算
        # Risk.assets.to_csv('asserts.csv')
        #
        plt=Risk.plot_future_assets_curve()
        #
        plt.show()

if __name__ == '__main__':
    test = Test_ActiveMove()
    test.main(1000)

