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
        self.asset = {}

    def buy(self, stock, amount):
        if stock not in self.asset:
            self.asset[stock] = amount
        else:
            self.asset[stock] += amount
        self.free_cash -= self.stock_prices[stock][-1]*amount

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
        pass

    @staticmethod
    def trade(fw, d, i):
        pass


class SimpleAgent(Agent):
    def __init__(self):
        super(SimpleAgent, self).__init__()

    def set_criteria(self):
        for stock in self.stocks:
            if stock in self.stock_prices:
                if len(self.stock_prices[stock]) >= 200:
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
            best[b] /= best_sum
        return best

    def set_stock_prices(self, prices):
        for stock in prices:
            if stock not in self.stock_prices:
                self.stock_prices[stock] = [prices[stock]]
            elif len(self.stock_prices[stock]) < 200:
                self.stock_prices[stock].append(prices[stock])
            else:
                self.stock_prices[stock].pop(0)
                self.stock_prices[stock].append(prices[stock])

    @staticmethod
    def trade(fw, d, i):
        agent.set_stock_prices(fw.get_stock_prices(d))
        if i >= 200:
            agent.set_criteria()
            portfolio = agent.strategy()
            # print(portfolio)
            if i == 200:
                for stck in portfolio:
                    agent.buy(stck, int(agent.balance * portfolio[stck] / agent.stock_prices[stck][-1]))
            else:
                current_asset = agent.asset.copy()
                for stck1 in portfolio:
                    for stck2 in current_asset:
                        if stck2 not in portfolio:
                            agent.sell(stck2, agent.asset[stck2])
                            if agent.asset[stck2] == 0:
                                agent.asset.pop(stck2)
                        if stck1 not in agent.asset:
                            agent.buy(stck1, int(agent.balance * portfolio[stck1] / agent.stock_prices[stck1][-1]))
                        if stck1 in agent.asset:
                            if int(agent.balance * portfolio[stck1] / agent.stock_prices[stck1][-1]) > \
                                    agent.asset[stck1]:
                                agent.buy(stck1, int(agent.balance * portfolio[stck1] / agent.stock_prices[stck1][-1]) -
                                          agent.asset[stck1])
                            elif int(agent.balance * portfolio[stck1] / agent.stock_prices[stck1][-1]) < \
                                    agent.asset[stck1]:
                                agent.sell(stck1, agent.asset[stck1] - int(agent.balance * portfolio[stck1] /
                                                                           agent.stock_prices[stck1][-1]))
                                if agent.asset[stck1] == 0:
                                    agent.asset.pop(stck1)
            agent.balance = sum([agent.asset[stck] * agent.stock_prices[stck][-1]
                                 for stck in agent.asset]) + agent.free_cash
            if i % 100 == 0:
                print(agent.balance, agent.free_cash, agent.asset)
        i += 1


if __name__ == '__main__':
    fin_world = spl.FinWorld(mode=None, period='10y', interval='1d', indices=['DAX', 'DJI'])
    agent = SimpleAgent()
    agent.set_stocks(fin_world.get_stocks())
    data = fin_world.tickers.tickers['GS'].history_data
    it = 0
    for day in data.index:
        day = str(day)
        day = day.split(' ')[0]
        agent.trade(fin_world, day, it)
    print(agent.balance, agent.free_cash, agent.asset)
