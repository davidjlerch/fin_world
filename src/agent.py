import stock_price_loader as spl
from operator import itemgetter
import numpy as np


class Agent:
    def __init__(self, name, balance=10000, asset_size=10, memory=200, expenses=0, trade_freq=1):
        self.stocks = []
        self.criteria = {}
        self.gain = {}
        self.stock_prices = {}
        self.balance = balance
        self.free_cash = balance
        self.asset_size = asset_size
        self.memory = memory
        self.expenses = expenses
        self.asset = {}
        self.trade_freq = trade_freq
        self.name = name

    def buy(self, stock, amount):
        if stock not in self.asset:
            self.asset[stock] = amount
        else:
            self.asset[stock] += amount
        self.free_cash -= self.stock_prices[stock][-1] * amount
        self.free_cash -= self.expenses
        self.balance -= self.expenses

    def sell(self, stock, amount):
        self.asset[stock] -= amount
        self.free_cash += self.stock_prices[stock][-1] * amount
        self.free_cash -= self.expenses
        self.balance -= self.expenses

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
            self._update_balance(stock)

    def _update_balance(self, stock):
        if stock in self.asset:
            self.balance += self.asset[stock] * (self.stock_prices[stock][-1] - self.stock_prices[stock][-2])

    def spend_rest(self):
        running = 1
        while running:
            running = 0
            for stock in self.asset:
                if self.free_cash > self.stock_prices[stock][-1]:
                    self.buy(stock, 1)
                    running = 1

    def trade(self, d, i):
        if i % self.trade_freq == 0:
            if i >= self.memory:
                self.set_criteria()
                portfolio = self.strategy()
                # update balance
                self.balance = sum([self.asset[stock] * self.stock_prices[stock][-1]
                                    for stock in self.asset]) + self.free_cash
                # trading margin for expenses
                total_balance = self.balance - self.expenses * self.asset_size
                # print(portfolio)
                if i == self.memory:
                    # initial buy
                    for stock in portfolio:
                        self.buy(stock, int(total_balance * portfolio[stock] / self.stock_prices[stock][-1]))
                else:
                    current_asset = self.asset.copy()
                    # if stock is removed from top list sell all
                    for stck2 in current_asset:
                        if stck2 not in portfolio and stck2 in self.asset:
                            self.sell(stck2, self.asset[stck2])
                            if self.asset[stck2] == 0:
                                self.asset.pop(stck2)
                    for stck1 in portfolio:
                        goal_amount = int(total_balance * portfolio[stck1] / self.stock_prices[stck1][-1])
                        if stck1 not in self.asset:
                            self.buy(stck1, goal_amount)
                        else:
                            if goal_amount > self.asset[stck1]:
                                self.buy(stck1, goal_amount - self.asset[stck1])
                            elif goal_amount < self.asset[stck1]:
                                self.sell(stck1, self.asset[stck1] - goal_amount + 1)
                                if self.asset[stck1] == 0:
                                    self.asset.pop(stck1)
                self.spend_rest()
                print(self.name, d, self.balance, self.free_cash, self.asset)
        if self.free_cash < 0:
            # print information for debugging
            """
            portfolio_sum = 0
            check_sum = 0
            checks = {}
            for stock in portfolio:
                goal_amount = int(total_balance * portfolio[stock] / self.stock_prices[stock][-1])
                print(goal_amount, '/', self.asset[stock])
                portfolio_sum += portfolio[stock]
                checks[stock] = self.asset[stock] * self.stock_prices[stock][-1] / self.balance
                check_sum += checks[stock]
            print(portfolio_sum, check_sum)
            print(portfolio)
            print(checks)
            """
            raise ValueError('You went bankrupt.')


class SimpleAgent(Agent):
    def __init__(self, balance=10000, asset_size=10, memory=200, expenses=0, trade_freq=1):
        super(SimpleAgent, self).__init__(balance=balance, asset_size=asset_size, memory=memory, expenses=expenses)
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
            best[b] /= (best_sum + 1e-4)
        return best

    def trade(self, fw, d, i):
        self.set_stock_prices(fw.get_stock_prices(d))
        if i % self.trade_freq == 0:
            if i >= self.memory:
                self.set_criteria()
                portfolio = self.strategy()
                total_balance = self.balance
                # print(portfolio)
                if i == self.memory:
                    self.free_cash -= self.expenses * self.asset_size
                    for stock in portfolio:
                        self.buy(stock, int(total_balance * portfolio[stock] / self.stock_prices[stock][-1]))
                else:
                    current_asset = self.asset.copy()
                    for stck2 in current_asset:
                        if stck2 not in portfolio and stck2 in self.asset:
                            self.free_cash -= self.expenses
                            self.sell(stck2, self.asset[stck2])
                            if self.asset[stck2] == 0:
                                self.asset.pop(stck2)
                    for stck1 in portfolio:
                        if stck1 not in self.asset:
                            self.free_cash -= self.expenses
                            self.buy(stck1, int(total_balance * portfolio[stck1] / self.stock_prices[stck1][-1]))
                        else:
                            if int(total_balance * portfolio[stck1] / self.stock_prices[stck1][-1]) > \
                                    self.asset[stck1]:
                                self.free_cash -= self.expenses
                                self.buy(stck1, int(total_balance * portfolio[stck1] /
                                                     self.stock_prices[stck1][-1]) -
                                          self.asset[stck1])
                            elif int(total_balance * portfolio[stck1] / self.stock_prices[stck1][-1]) < \
                                    self.asset[stck1]:
                                self.free_cash -= self.expenses
                                self.sell(stck1, self.asset[stck1] - int(total_balance * portfolio[stck1] /
                                                                           self.stock_prices[stck1][-1] + 1))
                                if self.asset[stck1] == 0:
                                    self.asset.pop(stck1)
                self.balance = sum([self.asset[stock] * self.stock_prices[stock][-1]
                                     for stock in self.asset]) + self.free_cash
                if i % 100 == 0:
                    print(d, self.balance, self.free_cash, self.asset)


if __name__ == '__main__':
    fin_world = spl.FinWorld(mode=None, period='5y', interval='1d', indices=['SPX', 'DAX', 'TDXP'])
    agent = SimpleAgent(trade_freq=20, expenses=5)
    all_stocks = fin_world.get_stocks()
    agent.set_stocks(stocks=all_stocks)
    data_len_max = 0
    for stck in all_stocks:
        data = fin_world.tickers.tickers[stck].history_data
        if len(data.index) > data_len_max:
            data_len_max = len(data.index)
    it = 0
    for day in data.index:
        day = str(day)
        day = day.split(' ')[0]
        agent.trade(fin_world, day, it)
        it += 1
    print(day, agent.balance, agent.free_cash, agent.asset)
