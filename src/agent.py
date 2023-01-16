from operator import itemgetter
import numpy as np
import pandas as pd
import dill
import time
import csv

try:
    import stock_price_loader as spl
except ImportError:
    import src.stock_price_loader as spl


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
        self.free_cash -= self.stock_prices[stock]['Open'][-1] * amount
        self.free_cash -= self.expenses
        self.balance -= self.expenses

    def sell(self, stock, amount):
        self.asset[stock] -= amount
        self.free_cash += self.stock_prices[stock]['Open'][-1] * amount
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
                self.stock_prices[stock] = {}
            for key in prices[stock]:
                if key not in self.stock_prices[stock]:
                    self.stock_prices[stock][key] = [prices[stock][key]]
                elif len(self.stock_prices[stock][key]) < self.memory:
                    self.stock_prices[stock][key].append(prices[stock][key])
                else:
                    self.stock_prices[stock][key].pop(0)
                    self.stock_prices[stock][key].append(prices[stock][key])
            self._update_balance(stock)

    def _update_balance(self, stock):
        if stock in self.asset:
            self.balance += self.asset[stock] * (self.stock_prices[stock]['Open'][-1] -
                                                 self.stock_prices[stock]['Open'][-2])

    def spend_rest(self):
        running = 1
        while running:
            running = 0
            for stock in self.asset:
                if self.free_cash - self.expenses > self.stock_prices[stock]['Open'][-1]:
                    self.buy(stock, 1)
                    running = 1

    def trade(self, d, i):
        if i % self.trade_freq == 0:
            if i >= self.memory:
                self.set_criteria()
                portfolio = self.strategy()
                # update balance
                self.balance = sum([self.asset[stock] * self.stock_prices[stock]['Open'][-1]
                                    for stock in self.asset]) + self.free_cash
                # trading margin for expenses and rest for next trading day
                total_balance = self.balance - self.expenses * (self.asset_size + 1)
                # print(portfolio)
                if i == self.memory:
                    # initial buy
                    for stock in portfolio:
                        self.buy(stock, int(total_balance * portfolio[stock] / self.stock_prices[stock]['Open'][-1]))
                else:
                    current_asset = self.asset.copy()
                    # if stock is removed from top list sell all
                    for stck2 in current_asset:
                        if stck2 not in portfolio and stck2 in self.asset:
                            self.sell(stck2, self.asset[stck2])
                            if self.asset[stck2] == 0:
                                self.asset.pop(stck2)
                    for stck1 in portfolio:
                        goal_amount = int(total_balance * portfolio[stck1] / self.stock_prices[stck1]['Open'][-1])
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
    def __init__(self, name, balance=10000, asset_size=10, memory=200, expenses=0, trade_freq=1, ma=30):
        super(SimpleAgent, self).__init__(name, balance=balance, asset_size=asset_size, memory=memory, expenses=expenses,
                                          trade_freq=trade_freq)
        self.ma = ma

    def set_criteria(self):
        for stock in self.stock_prices:
            if len(self.stock_prices[stock]['Open']) >= self.memory:
                # print(len(self.stock_prices[stock]['Open'][-30:]))
                self.criteria[stock] = [sum(self.stock_prices[stock]['Open'][-self.ma:]) / sum(self.stock_prices[stock]['Open'])]

    def strategy(self):
        for stock in self.criteria:
            self.gain[stock] = sum(self.criteria[stock])
        best = dict(sorted(self.gain.items(), key=itemgetter(1), reverse=True)[:self.asset_size])
        # print(best)
        best_sum = 0
        for b in best:
            best_sum += best[b]
        for b in best:
            best[b] /= (best_sum + 1e-4)
        return best


class MATrendAgent(Agent):
    def __init__(self, name, balance=10000, asset_size=10, memory=200, expenses=0, trade_freq=1, ma=30, trend=30):
        super(MATrendAgent, self).__init__(name, balance=balance, asset_size=asset_size, memory=memory,
                                           expenses=expenses, trade_freq=trade_freq)
        self.ma = ma
        self.trend = trend

    def set_criteria(self):
        for stock in self.stock_prices:
            if len(self.stock_prices[stock]['Open']) >= self.memory:
                self.criteria[stock] = [np.polyfit(np.linspace(0, self.trend-1, self.trend),
                                                   self.stock_prices[stock]['Open'][-self.trend:], 1)[1] /
                                        np.mean(self.stock_prices[stock]['Open'][-self.trend:]) *
                                        sum(self.stock_prices[stock]['Open'][-self.ma:]) / sum(self.stock_prices[stock]['Open'])]

    def strategy(self):
        for stock in self.criteria:
            self.gain[stock] = sum(self.criteria[stock])
        best = dict(sorted(self.gain.items(), key=itemgetter(1), reverse=True)[:self.asset_size])
        # print(best)
        best_sum = 0
        for b in best:
            best_sum += best[b]
        for b in best:
            best[b] /= (best_sum + 1e-4)
        return best


class MmtAgent(Agent):
    def __init__(self, name, balance=10000, asset_size=10, memory=200, expenses=0, trade_freq=1, momentum=1, ma=1):
        super(MmtAgent, self).__init__(name, balance=balance, asset_size=asset_size, memory=memory,
                                       expenses=expenses, trade_freq=trade_freq)
        self.momentum = momentum
        self.ma = ma

    def set_criteria(self):
        for stock in self.stock_prices:
            if len(self.stock_prices[stock]['Open']) >= self.memory:
                self.criteria[stock] = [np.mean(self.stock_prices[stock]['Open'][-self.ma:]) /
                                        np.mean(self.stock_prices[stock]['Open'][:(-self.momentum+self.ma)])]

    def strategy(self):
        for stock in self.criteria:
            self.gain[stock] = sum(self.criteria[stock])
        best = dict(sorted(self.gain.items(), key=itemgetter(1), reverse=True)[:self.asset_size])
        # print(best)
        best_sum = 0
        for b in best:
            best_sum += best[b]
        for b in best:
            best[b] /= (best_sum + 1e-4)
        return best


class BollingerAgent(Agent):
    def __init__(self, name, balance=10000, asset_size=10, memory=200, expenses=0, trade_freq=1, ma=20, k=2):
        super(BollingerAgent, self).__init__(name, balance=balance, asset_size=asset_size, memory=memory,
                                             expenses=expenses, trade_freq=trade_freq)
        self.ma = ma
        self.k = k

    def bollinger_band(self, stock):
        prices = self.stock_prices[stock]['Open'][-self.ma:]
        sig = np.std(prices)
        mu = np.mean(prices)
        return mu - self.k * sig, mu + self.k * sig, mu

    def set_criteria(self):
        for stock in self.stock_prices:
            # print(stock, self.stock_prices[stock])
            if len(self.stock_prices[stock]['Open']) >= self.memory:
                boll_min, boll_max, mean = self.bollinger_band(stock)
                self.criteria[stock] = [boll_max / boll_min * self.stock_prices[stock]['Open'][-1] / mean]

    def strategy(self):
        for stock in self.criteria:
            self.gain[stock] = sum(self.criteria[stock])
        best = dict(sorted(self.gain.items(), key=itemgetter(1), reverse=True)[:self.asset_size])
        # print(best)
        best_sum = 0
        for b in best:
            best_sum += best[b]
        for b in best:
            best[b] /= (best_sum + 1e-4)
        return best


class ADXAgent(Agent):
    def __init__(self, name, source_agent, balance=10000, asset_size=10, memory=200, expenses=0, trade_freq=1,
                 ma=1):
        super(ADXAgent, self).__init__(name, balance=balance, asset_size=asset_size, memory=memory,
                                       expenses=expenses, trade_freq=trade_freq)
        self.source_agent = source_agent
        self.ma = ma
        self.tr = {}
        self.dm = {}
        self.di = {}
        self.adx = {}
        self.sign = {}

    def set_tr(self, stock):
        if stock not in self.tr:
            self.tr[stock] = [np.max([self.stock_prices[stock]['High'][-1] - self.stock_prices[stock]['Low'][-1],
                                      self.stock_prices[stock]['High'][-1] - self.stock_prices[stock]['Close'][-2],
                                      self.stock_prices[stock]['Close'][-2] - self.stock_prices[stock]['Low'][-1]])]

        else:
            if len(self.tr[stock]) > self.ma:
                self.tr[stock].pop(0)
            self.tr[stock].append(np.max([self.stock_prices[stock]['High'][-1] -
                                          self.stock_prices[stock]['Low'][-1],
                                          self.stock_prices[stock]['High'][-1] -
                                          self.stock_prices[stock]['Close'][-2],
                                          self.stock_prices[stock]['Close'][-2] -
                                          self.stock_prices[stock]['Low'][-1]]))

    def set_dm(self, stock):
        if stock not in self.dm:
            self.dm[stock] = [[self.stock_prices[stock]['High'][-1] - self.stock_prices[stock]['High'][-2],
                               self.stock_prices[stock]['Low'][-2] - self.stock_prices[stock]['Low'][-1]]]
        else:
            if len(self.dm[stock]) > self.ma:
                self.dm[stock].pop(0)
            self.dm[stock].append([self.stock_prices[stock]['High'][-1] - self.stock_prices[stock]['High'][-2],
                                   self.stock_prices[stock]['Low'][-2] - self.stock_prices[stock]['Low'][-1]])

    def set_di(self, stock):
        ema = pd.DataFrame(self.dm[stock]).ewm(com=0., axis=1).mean().values[0]
        atr = np.mean(self.tr[stock]) + 1e-8
        di = ema / atr
        if stock not in self.di:
            self.di[stock] = [(di[0] - di[1]) / (di[0] + di[1] + 1e-8)]
        else:
            if len(self.di[stock]) > self.ma:
                self.di[stock].pop(0)
            self.di[stock].append((di[0] - di[1]) / (di[0] + di[1] + 1e-8))
        return di

    def set_adx(self, stock):
        self.set_tr(stock)
        self.set_dm(stock)
        di = self.set_di(stock)
        adx_new = sum(self.di[stock])
        if stock in self.adx:
            if self.adx[stock] < 25 < adx_new:
                if di[0] > di[1]:
                    self.sign[stock] = 1
                elif di[0] < di[1]:
                    self.sign[stock] = 0
        self.adx[stock] = adx_new

    def set_stock_prices(self, prices):
        for stock in prices:
            if stock not in self.stock_prices:
                self.stock_prices[stock] = {}
            for key in prices[stock]:
                if key not in self.stock_prices[stock]:
                    self.stock_prices[stock][key] = [prices[stock][key]]
                elif len(self.stock_prices[stock][key]) < self.memory:
                    self.stock_prices[stock][key].append(prices[stock][key])
                else:
                    self.stock_prices[stock][key].pop(0)
                    self.stock_prices[stock][key].append(prices[stock][key])
            if len(self.stock_prices[stock][key]) > 1:
                self.set_adx(stock)
            self._update_balance(stock)

    def set_criteria(self):
        for stock in self.source_agent.asset:
            if stock in self.sign:
                self.criteria[stock] = [self.sign[stock] * self.source_agent.criteria[stock][0]]

    def strategy(self):
        for stock in self.criteria:
            self.gain[stock] = sum(self.criteria[stock])
        best = dict(sorted(self.gain.items(), key=itemgetter(1), reverse=True)[:self.asset_size])
        # print(best)
        best_sum = 0
        for b in best:
            best_sum += best[b]
        for b in best:
            best[b] /= (best_sum + 1e-4)
        return best


class CopyAgent(Agent):
    def __init__(self, name, agent_list, balance=10000, asset_size=10, memory=200, expenses=0, trade_freq=1):
        super(CopyAgent, self).__init__(name, balance=balance, asset_size=asset_size, memory=memory,
                                        expenses=expenses, trade_freq=trade_freq)
        self.agent_list = agent_list

    def set_criteria(self):
        for agnt in self.agent_list:
            for stock in agnt.asset:
                if stock in self.criteria:
                    self.criteria[stock] += [agnt.balance * agnt.asset[stock]]
                else:
                    self.criteria[stock] = [agnt.balance * agnt.asset[stock]]

    def strategy(self):
        for stock in self.criteria:
            self.gain[stock] = sum(self.criteria[stock])
        self.criteria = {}
        best = dict(sorted(self.gain.items(), key=itemgetter(1), reverse=True)[:self.asset_size])
        # print(best)
        best_sum = 0
        for b in best:
            best_sum += best[b]
        for b in best:
            best[b] /= (best_sum + 1e-4)
        return best


if __name__ == '__main__':
    fin_world = spl.FinWorld(mode=None, period='1y', interval='1d', indices=['SPX', 'TDXP', 'MDAX', 'SDXP', 'DAX'])         # 'OEX', 'SPX', 'TDXP', 'MDAX', 'SDXP'
    agent1 = SimpleAgent('Simple30', trade_freq=15, expenses=0)
    # agent2 = SimpleAgent('Simple15', trade_freq=15, expenses=3, ma=15)
    agent3 = MATrendAgent('MATrend30', trade_freq=15, expenses=0)
    agent2 = BollingerAgent('Bollinger30', trade_freq=15, expenses=0)
    # agent3 = MmtAgent('Momentum50', trade_freq=15, expenses=3, momentum=50)
    agent4 = MmtAgent('Momentum200', trade_freq=15, expenses=0, momentum=200)
    # agent6 = MmtAgent('Momentum200', trade_freq=5, expenses=3, momentum=200)

    agents = [agent1, agent2, agent3, agent4]
    all_stocks = fin_world.get_stocks()
    for agent in agents:
        agent.set_stocks(stocks=all_stocks)

    data_len_max = [0]
    for stck in all_stocks:
        data = fin_world.tickers.tickers[stck].history_data
        if len(data.index) > len(data_len_max):
            data_len_max = data.index
    it = 0
    for day in data.index:
        day = str(day)
        day = day.split(' ')[0]
        for agent in agents:
            agent.set_stock_prices(fin_world.get_stock_prices(day))
            agent.trade(day, it)
        it += 1
    for agent in agents:
        print(agent.name, day, agent.balance, agent.free_cash, agent.asset)

