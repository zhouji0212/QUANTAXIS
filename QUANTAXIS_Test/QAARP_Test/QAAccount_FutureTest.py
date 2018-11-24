import random as rnd
import unittest

import QUANTAXIS as QA


class Test_FutureAccount(unittest.TestCase):

    def test_future(self):
        b = QA.QA_BacktestBroker()
        data = QA.QA_fetch_future_day_adv('RBL8','2018-10-20','2018-11-04')
        account = QA.QA_Account(init_cash=100000,allow_sellopen=True, allow_t0=True,
                            market_type=QA.MARKET_TYPE.FUTURE_CN,
                            frequence=QA.FREQUENCE.DAY,margin_rate=0.1)
        buy_sell = [QA.ORDER_DIRECTION.SELL_OPEN,QA.ORDER_DIRECTION.BUY_CLOSE,QA.ORDER_DIRECTION.BUY_OPEN,QA.ORDER_DIRECTION.SELL_CLOSE]
        i = 0
        for items in data.panel_gen:
            for item in items.security_gen:

                date = item.index
                order = account.send_order(
                    code=item.index[0][1],
                    time=item.index[0][0],
                    towards= buy_sell[i%4],
                    price=item.get('close')[0],
                    order_model=QA.ORDER_MODEL.CLOSE,
                    amount_model=QA.AMOUNT_MODEL.BY_AMOUNT,
                    amount=10
                )
                event = QA.QA_Event(order= order,market_data=item)
                print(event)
                print(b.receive_order(event))
                trade_msg = b.query_orders(account.account_cookie,'filled')
                res = trade_msg.loc[order.account_cookie,order.realorder_id]
                print(res)
                #order.trade(res.trade_id,res.trade_price,res.trade_ammount,res.trade_time)
                account.receive_deal(res.code, res.trade_id, str(i), str(i),
                              res.trade_price, res.trade_amount, res.towards, res.trade_time)
                i =i+1
                account.settle()
                print(account.future_total_hold)
        account.history_table.to_clipboard()