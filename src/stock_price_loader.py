import yfinance as yf
import stocksymbol as ss
import settings


class FinWorld:
    def __init__(self):
        ssy = ss.StockSymbol(settings.api_key)
        self._lst_us = ssy.get_symbol_list(market='us')
        self._lst_de = ssy.get_symbol_list(market='de')
        self._create_tickers()

    def _create_tickers(self):
        for stock in self._lst_us:
            dvn = stock['symbol'].lower()
            setattr(self, dvn, yf.Ticker(dvn))
        for stock in self._lst_de:
            dvn = stock['symbol'].lower()
            setattr(self, dvn, yf.Ticker(dvn))

# symbl_lst_de = [stock['symbol'] for stock in lst_de]
# print(ssy.index_list)


if __name__ == '__main__':
    fw = FinWorld()
    print(fw.msft.balance_sheet)
