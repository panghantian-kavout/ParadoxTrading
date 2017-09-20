import cmd
import configparser
import logging
from pprint import pprint

from ParadoxTrading.Engine import ActionType, DirectionType
from ParadoxTrading.Utils.CTP import CTPTraderSpi

logging.basicConfig(level=logging.INFO)


class CTPCMD(cmd.Cmd):
    prompt = '>>> '

    def __init__(self, _config):
        super().__init__()

        self.trader = CTPTraderSpi(
            config['TRADE']['ConPath'].encode(),
            # b'tcp://180.168.146.187:10030',
            config['TRADE']['Front'].encode(),
            config['TRADE']['BrokerID'].encode(),
            config['TRADE']['UserID'].encode(),
            config['TRADE']['Password'].encode(),
        )

    def emptyline(self):
        pass

    def do_connect(self, arg):
        'Connect to front'
        self.trader.Connect()

    def do_login(self, arg):
        'Log in'
        self.trader.ReqUserLogin()

    def do_instrument(self, arg):
        'Fetch all instrument info'
        print(self.trader.ReqQryInstrument())

    def do_position(self, arg):
        'Fetch all position info'
        print(self.trader.ReqQryInvestorPosition())

    def do_order(self, arg):
        print(self.trader.ReqQryOrder())

    def do_trade(self, arg):
        print(self.trader.ReqQryTrade())

    def do_market(self, arg):
        'Fetch instrument depth market data: market rb1801'
        pprint(self.trader.ReqQryDepthMarketData(arg.encode()))

    @staticmethod
    def _split_arg(_arg):
        instrument, volume, price = _arg.split()
        instrument = instrument.encode()
        volume = int(volume)
        price = float(price)
        return instrument, volume, price

    def do_open_buy(self, arg):
        instrument, volume, price = CTPCMD._split_arg(arg)
        pprint(self.trader.ReqOrderInsert(
            instrument, DirectionType.BUY, ActionType.OPEN,
            volume, price
        ))

    def do_open_sell(self, arg):
        instrument, volume, price = CTPCMD._split_arg(arg)
        pprint(self.trader.ReqOrderInsert(
            instrument, DirectionType.SELL, ActionType.OPEN,
            volume, price
        ))

    def do_close_buy(self, arg):
        instrument, volume, price = CTPCMD._split_arg(arg)
        pprint(self.trader.ReqOrderInsert(
            instrument, DirectionType.BUY, ActionType.CLOSE,
            volume, price
        ))

    def do_close_sell(self, arg):
        instrument, volume, price = CTPCMD._split_arg(arg)
        pprint(self.trader.ReqOrderInsert(
            instrument, DirectionType.SELL, ActionType.CLOSE,
            volume, price
        ))

    def do_close_buy_today(self, arg):
        instrument, volume, price = CTPCMD._split_arg(arg)
        pprint(self.trader.ReqOrderInsert(
            instrument, DirectionType.BUY, ActionType.CLOSE,
            volume, price, _today=True
        ))

    def do_close_sell_today(self, arg):
        instrument, volume, price = CTPCMD._split_arg(arg)
        pprint(self.trader.ReqOrderInsert(
            instrument, DirectionType.SELL, ActionType.CLOSE,
            volume, price, _today=True
        ))

    def do_account(self, arg):
        pprint(self.trader.ReqQryTradingAccount())

    def do_commission_rate(self, arg):
        pprint(self.trader.ReqQryInstrumentCommissionRate(arg.encode()))

    def do_settlement_confirm(self, arg):
        self.trader.ReqSettlementInfoConfirm()

    def do_quit(self, arg):
        return True


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('./config.ini')
    CTPCMD(config).cmdloop()
