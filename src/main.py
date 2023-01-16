import csv
import time
import dill

from src.agent import MATrendAgent, MmtAgent, CopyAgent
from src import stock_price_loader as spl


def main(fin_world, agents, data):
    it = 0
    field_names = [agent.name for agent in agents]
    with open(path, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=field_names, delimiter=';')
        writer.writeheader()
        for day in data.index:
            day = str(day)
            day = day.split(' ')[0]
            stock_prices_today = fin_world.get_stock_prices(day)
            today_dict = {}
            for agent in agents:
                agent.set_stock_prices(stock_prices_today)
                agent.trade(day, it)
                today_dict[agent.name] = agent.balance
            writer.writerow(today_dict)
            it += 1
    for agent in agents:
        print(agent.name, day, agent.balance, agent.free_cash, agent.asset)


if __name__ == '__main__':
    fin_world_ = spl.FinWorld(mode=None, period='1y', interval='1d',
                              indices=['SPX', 'TDXP', 'MDAX', 'SDXP', 'DAX'])  # 'OEX', 'SPX', 'TDXP', 'MDAX', 'SDXP'
    # with open('fin_world_new.pkl', 'wb') as out_f:
    #     fin_world = dill.dump(fin_world, out_f)

    path = str(time.time()) + '_agents_results.csv'

    # with open('fin_world.pkl', 'rb') as in_f:
    #     fin_world = dill.load(in_f)

    memory_ = 200
    balance = 20000
    # agent2 = SimpleAgent('Simple15', trade_freq=15, expenses=3, ma=15)
    agent3 = MATrendAgent('MATrend30/5/15', balance=balance, trade_freq=1, expenses=0, memory=memory_, ma=5)
    agent2 = MmtAgent('Momentum200/5/15', balance=balance, trade_freq=1, expenses=0, momentum=200, memory=memory_, ma=5)
    # agent6 = MATrendAgent('MATrend30/5/5', balance=balance, trade_freq=1, expenses=0, memory=memory_, ma=5)
    # agent5 = MmtAgent('Momentum200/5/5', balance=balance, trade_freq=1, expenses=0, momentum=200, memory=memory_, ma=5)
    # agent1 = MmtAgent('Momentum195/5', balance=balance, trade_freq=1, expenses=0, momentum=195, memory=memory_, ma=5)
    agent4 = CopyAgent('CopyOrig', balance=balance, agent_list=[agent2, agent3], trade_freq=1, expenses=0,
                       memory=memory_)

    agents_ = [agent2, agent3, agent4]
    all_stocks = fin_world_.get_stocks()
    for agent_ in agents_:
        agent_.set_stocks(stocks=all_stocks)
    data_len_max = [0]
    for stck in all_stocks:
        data0 = fin_world_.tickers.tickers[stck].history_data
        if len(data0.index) > len(data_len_max):
            data_len_max = data0.index
            data_ = data0
    main(fin_world_, agents_, data_)
