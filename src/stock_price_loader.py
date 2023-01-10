import yfinance as yf
import stocksymbol as ss
import time
from tqdm import tqdm

try:
    import settings as settings
except ImportError:
    import src.settings as settings


class FinWorld:
    def __init__(self, mode, period='', interval='', indices=[]):
        # create a settings file and store your stocksymbol api key https://stock-symbol.herokuapp.com/
        # in api_key variable
        ssy = ss.StockSymbol(settings.api_key)
        # print(ssy.market_list)
        self.lsts = []
        for index in indices:
            self.lsts += ssy.get_symbol_list(index=index)
        self._time = None
        self.mode = mode
        self.period = period
        self.interval = interval

        self._create_tickers()

    def _create_tickers(self):
        symbls = ''
        for symbl in tqdm(self.lsts, desc="Loading...", total=len(self.lsts)):
            symbls += symbl['symbol']
            if symbl != self.lsts[-1]:
                symbls += ' '
        # print(symbls)
        self.tickers = yf.Tickers(symbls)
        self._download_data()

    def _download_data(self):
        for sbl in tqdm(self.tickers.symbols, desc="Loading...", total=len(self.tickers.symbols)):
            self.tickers.tickers[sbl].history_data = self.tickers.tickers[sbl].history(period=self.period,
                                                                                       interval=self.interval)

    def set_current_time(self):
        self._time = time.time()

    def get_time(self):
        return self._time

    def get_stocks(self):
        return self.tickers.symbols

    def get_stock_prices(self, day):
        stock_prices = {}
        for sbl in self.tickers.symbols:
            for p in range(10):
                try:
                    stock_prices[sbl] = self.tickers.tickers[sbl].history_data.loc[day + ' 00:00:00+0' + str(p) +
                                                                                   ':00', 'Open']
                    break
                except:
                    try:
                        stock_prices[sbl] = self.tickers.tickers[sbl].history_data.loc[day + ' 00:00:00-0' +
                                                                                       str(p) + ':00', 'Open']
                        break
                    except:
                        pass
        return stock_prices


if __name__ == '__main__':
    fw = FinWorld(mode=None, period='10y', interval='1d', indices=['DAX', 'DJI'])
    print(fw.tickers.tickers['GS'].history_data)
