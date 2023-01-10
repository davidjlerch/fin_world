import agent as agent
import stock_price_loader as spl
import multiprocessing
import time


def process(q, pck):
    all_stocks, trd_frq = pck
    my_agent = agent.SimpleAgent(trade_freq=trd_frq, expenses=3)
    my_agent.set_stocks(stocks=all_stocks)
    prices, day, it = q.get()
    my_agent.set_stock_prices(prices)
    my_agent.trade(day, it)


def main():
    fin_world = spl.FinWorld(mode=None, period='5y', interval='1d', indices=['OEX', 'DAX', 'TDXP'])
    all_stocks = fin_world.get_stocks()
    data_len_max = [0]
    for stck in all_stocks:
        data = fin_world.tickers.tickers[stck].history_data
        if len(data.index) > len(data_len_max):
            data_len_max = data.index
    pcks = [[all_stocks, 5], [all_stocks, 10],
            [all_stocks, 30], [all_stocks, 100]]
    q = [multiprocessing.Queue() for _ in range(len(pcks))]

    p = [multiprocessing.Process(target=process, args=(q[i], pcks[i])) for i in range(len(q))]
    for p_ in p:
        p_.start()
    it = 0
    print('Started trading..')
    start_time = time.time()
    for day in data_len_max:
        day = str(day)
        day = day.split(' ')[0]
        for q_ in q:
            q_.put([fin_world.get_stock_prices(day), day, it])
        it += 1
        if it % 100 == 0:
            print((time.time()-start_time)/it)
    for p_ in p:
        p_.join()


if __name__ == '__main__':
    main()
