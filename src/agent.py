import stock_price_loader as spl
from operator import itemgetter


class Agent:
    def __init__(self):
        self.stocks = []
        self.criteria = {}
        self.gain = {}
        self.stock_prices = {}
        self.balance = 10000
        self.free_cash = 10000
        self.asset_size = 10
        self.memory = 200
        self.expenses = 0
        self.asset = {}

    def buy(self, stock, amount):
        if stock not in self.asset:
            self.asset[stock] = amount
        else:
            self.asset[stock] += amount
        self.free_cash -= self.stock_prices[stock][-1] * amount

    def sell(self, stock, amount):
        self.asset[stock] -= amount
        self.free_cash += self.stock_prices[stock][-1] * amount

    def set_criteria(self):
        pass

    def strategy(self):
        pass

    def set_stocks(self, stocks):
        self.stocks = stocks

    def set_stock_prices(self, prices):
        for stock in prices:
            if stock not in self.stock_prices:
                self.stock_prices[stock] = [prices[stock]]
            elif len(self.stock_prices[stock]) < self.memory:
                self.stock_prices[stock].append(prices[stock])
            else:
                self.stock_prices[stock].pop(0)
                self.stock_prices[stock].append(prices[stock])
            self.update_balance(stock)

    def update_balance(self, stock):
        if stock in self.asset:
            self.balance += self.asset[stock] * (self.stock_prices[stock][-1] - self.stock_prices[stock][-2])

    def trade(self, fw, d, i):
        pass


class SimpleAgent(Agent):
    def __init__(self, trade_freq=1):
        super(SimpleAgent, self).__init__()
        self.trade_freq = trade_freq

    def set_criteria(self):
        for stock in self.stocks:
            if stock in self.stock_prices:
                if len(self.stock_prices[stock]) >= self.memory:
                    # print(len(self.stock_prices[stock][-30:]))
                    self.criteria[stock] = [(sum(self.stock_prices[stock][-30:]) / len(self.stock_prices[stock][-30:]) -
                                             sum(self.stock_prices[stock]) / len(self.stock_prices[stock])) /
                                            self.stock_prices[stock][-1]]

    def strategy(self):
        for stock in self.stocks:
            if stock in self.criteria:
                self.gain[stock] = sum(self.criteria[stock])
        best = dict(sorted(self.gain.items(), key=itemgetter(1), reverse=True)[:self.asset_size])
        # print(best)
        best_sum = 0
        for b in best:
            best_sum += best[b]
        for b in best:
            best[b] /= (best_sum + 1)
        return best

    def trade(self, fw, d, i):
        agent.set_stock_prices(fw.get_stock_prices(d))
        if i % self.trade_freq == 0:
            if i >= self.memory:
                agent.set_criteria()
                portfolio = agent.strategy()
                total_balance = agent.balance
                # print(portfolio)
                if i == self.memory:
                    self.free_cash -= self.expenses * self.asset_size
                    for stock in portfolio:
                        agent.buy(stock, int(total_balance * portfolio[stock] / agent.stock_prices[stock][-1]))
                else:
                    current_asset = agent.asset.copy()
                    for stck2 in current_asset:
                        if stck2 not in portfolio and stck2 in agent.asset:
                            self.free_cash -= self.expenses
                            agent.sell(stck2, agent.asset[stck2])
                            if agent.asset[stck2] == 0:
                                agent.asset.pop(stck2)
                    for stck1 in portfolio:
                        if stck1 not in agent.asset:
                            self.free_cash -= self.expenses
                            agent.buy(stck1, int(total_balance * portfolio[stck1] / agent.stock_prices[stck1][-1]))
                        else:
                            if int(total_balance * portfolio[stck1] / agent.stock_prices[stck1][-1]) > \
                                    agent.asset[stck1]:
                                self.free_cash -= self.expenses
                                agent.buy(stck1, int(total_balance * portfolio[stck1] /
                                                     agent.stock_prices[stck1][-1]) -
                                          agent.asset[stck1])
                            elif int(total_balance * portfolio[stck1] / agent.stock_prices[stck1][-1]) < \
                                    agent.asset[stck1]:
                                self.free_cash -= self.expenses
                                agent.sell(stck1, agent.asset[stck1] - int(total_balance * portfolio[stck1] /
                                                                           agent.stock_prices[stck1][-1] + 1))
                                if agent.asset[stck1] == 0:
                                    agent.asset.pop(stck1)
                agent.balance = sum([agent.asset[stock] * agent.stock_prices[stock][-1]
                                     for stock in agent.asset]) + agent.free_cash
                if i % 100 == 0:
                    print(day, agent.balance, agent.free_cash, agent.asset)
            if agent.free_cash < 0:
                print(agent.free_cash, '\n', agent.balance, '\n', agent.asset, '\n', portfolio, '\n',
                      [agent.stock_prices[stock][-1] for stock in portfolio])
                raise Exception(i)


if __name__ == '__main__':
    fin_world = spl.FinWorld(mode=None, period='5y', interval='1d', indices=['SPX', 'DAX', 'TDXP'])
    agent = SimpleAgent(trade_freq=20)
    all_stocks = fin_world.get_stocks()
    agent.set_stocks(stocks=all_stocks)
    data_len_max = 0
    for stck in all_stocks:
        data = fin_world.tickers.tickers[stck].history_data
        if len(data.index) > data_len_max:
            data_len_max = len(data.index)
    del stck
    it = 0
    for day in data.index:
        day = str(day)
        day = day.split(' ')[0]
        agent.trade(fin_world, day, it)
        it += 1
    print(day, agent.balance, agent.free_cash, agent.asset)
