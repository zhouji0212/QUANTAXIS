import random as rnd
import unittest

import QUANTAXIS as QA
import random

class Test_FutureAccount(unittest.TestCase):

    # def __init__(self):
    #     super(Test_FutureAccount,self).__init__()

    def test_future(self):
        self.b = QA.QA_BacktestBroker()
        self.data = QA.QA_fetch_future_day_adv('RBL8', '2018-10-1', '2018-11-10')
        self.account = QA.QA_Account(init_cash=100000, allow_sellopen=True, allow_t0=True,
                                     market_type=QA.MARKET_TYPE.FUTURE_CN,
                                     frequence=QA.FREQUENCE.DAY, margin_rate=0.1)
        buy_sell = [QA.ORDER_DIRECTION.SELL_OPEN,QA.ORDER_DIRECTION.BUY_CLOSE,QA.ORDER_DIRECTION.BUY_OPEN,QA.ORDER_DIRECTION.SELL_CLOSE]
        i = 0
        for items in self.data.panel_gen:
            for item in items.security_gen:
                code = item.index[0][0]
                date = item.index[0][1]

                order = self.GenOrder(item,random.choice(buy_sell),10)
                self.SendOrder(order,item)
                i =i+1
                self.account.settle()
                print(self.account.hold_available)
                print(self.account.future_hold_detail)
                # if(self.account.hold_available[code][QA.ORDER_DIRECTION.BUY_OPEN]!=0):
                #     print('1111')

        self.account.history_table.to_clipboard()

    def GenOrder(self,day_product, offset, volume):
        return self.account.send_order(
            code=day_product.index[0][1],
            time=day_product.index[0][0],
            amount=volume,
            towards=offset,
            price=day_product.price.iloc[0],
            order_model=QA.ORDER_MODEL.CLOSE,
            amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
        )



    def SendOrder(self,order,day_product):
        event = QA.QA_Event(order=order, market_data=day_product)
        rec_msg = self.b.receive_order(event)
        trade_mes = self.b.query_orders(self.account.account_cookie, 'filled')
        res = trade_mes.iloc[0]
        msg = order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)
        # self.account.receive_deal(res.code, res.trade_id, str(i), str(i),
        #                           res.trade_price, res.trade_amount, res.towards, res.trade_time)
        print('sendorder', msg)