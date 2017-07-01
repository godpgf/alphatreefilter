#coding=utf-8
#author=godpgf
#作为alphatree和stock data之间的中介

from stdb.data_reader import date2int
import numpy as np
import random


def get_alphatree_data(sample_stock_list, day_index_list, stock_all, max_date = 520, watch_future_size = 5):
    score_list = get_score_list(sample_stock_list, day_index_list, watch_future_size)
    #real_score_list = get_real_score_list(sample_stock_list, day_index_list, watch_future_size)
    stock_all_dict = {}
    for s in stock_all:
        stock_all_dict[s[0]] = s
    #todo 加入行业
    leaf_dict = dict()
    set_stock_dict(leaf_dict, sample_stock_list, day_index_list, "", max_date)
    comp_stock_list = get_compare_stock_list(sample_stock_list, day_index_list, stock_all_dict, max_date)
    comp_day_index_list = [max_date] * len(comp_stock_list)
    set_stock_dict(leaf_dict, comp_stock_list, comp_day_index_list,'IndClass.subindustry:', max_date)
    set_stock_dict(leaf_dict, comp_stock_list, comp_day_index_list, 'IndClass.sector:', max_date)
    set_stock_dict(leaf_dict, comp_stock_list, comp_day_index_list, 'IndClass.industry:', max_date)
    leaf_dict['score'] = score_list

    return leaf_dict

def get_current_alphatree_data(cur_stock_list, cur_code_list, stock_all, max_date):
    #todo
    stock_all_dict = {}
    for s in stock_all:
        stock_all_dict[s[0]] = s

    leaf_dict = dict()
    day_index_list = [len(cur_stock_list[i])-1 for i in xrange(len(cur_code_list))]

    for i in xrange(len(cur_stock_list)):
        assert cur_stock_list[i]["volume"][-1] != 0
        if i > 0:
            assert cur_stock_list[i]["date"][-1] == cur_stock_list[i-1]["date"][-1]

    set_stock_dict(leaf_dict, cur_stock_list, day_index_list, "", max_date)
    comp_stock_list = get_compare_stock_list(cur_stock_list, day_index_list, stock_all_dict, max_date)
    comp_day_index_list = [max_date] * len(comp_stock_list)
    set_stock_dict(leaf_dict, comp_stock_list, comp_day_index_list,'IndClass.subindustry:', max_date)
    set_stock_dict(leaf_dict, comp_stock_list, comp_day_index_list, 'IndClass.sector:', max_date)
    set_stock_dict(leaf_dict, comp_stock_list, comp_day_index_list, 'IndClass.industry:', max_date)
    leaf_dict['code'] = cur_code_list
    return leaf_dict


#读取近期股票数据
def read_stock_list(codeProxy, dataProxy, max_date = 260, cur_date = None):
    stockList = list()
    codeList = list()
    codes = codeProxy.get_codes()
    if cur_date:
        cur_date = 1000000*date2int(cur_date)
    for code in codes:
        print "code:%s,%d"%(code[0],len(code[0]))
        data = dataProxy.get_all_Data(code[0])

        if data is not None:
            if cur_date:
                data = data[np.where(data['date'] <= cur_date)]
            if len(data[np.where(data['volume'] > 0)]) > max_date:
                codeList.append(code)
                stockList.append(data)
    return stockList, codeList, dataProxy.get_all_Data('0000001')

def filter_current_stock_list(stock_list, code_list, stock_all, max_date = 260):
    new_stock_list = []
    new_code_list = []
    for i in xrange(len(stock_list)):
        data = stock_list[i][-max_date-1:]
        if data['date'][-1] == stock_all['date'][-1] and len(data[np.where(data['volume'] > 0)]) >= max_date * 0.8 and data['volume'][-1] > 0:
            new_stock_list.append(stock_list[i])
            new_code_list.append(code_list[i])
    return new_stock_list, new_code_list

#def get_eval_score(stock, index, watch_future_size, deposit_rate = 0.8):
#    score = stock['rise'][index]
#    r = deposit_rate
#    for i in xrange(1,watch_future_size+1):
#        score += stock['rise'][index + i] * r
#        r *= deposit_rate
#    return score

def get_score(stock, index, watch_future_size):
    cur_price = stock['close'][index]
    score = (stock['close'][index + watch_future_size] - cur_price)/cur_price
    return score

def sample_stock(stock_list, watch_future_size = 5, history_day=160, sample_size=960, max_date = 260):
    day_index_list = list()
    sample_stock_list = list()
    #score_list = list()
    random_stock_list = stock_list[:]
    random.shuffle(random_stock_list)

    #sample_stock_list = sample_stock_list[:sample_size]
    sum_returns = 0
    for i in xrange(len(random_stock_list)):
        min_index = max(len(random_stock_list[i]) - history_day - watch_future_size, max_date)
        max_index = len(random_stock_list[i]) - 1 - watch_future_size
        while random_stock_list[i]['volume'][min_index] == 0 or random_stock_list[i]['volume'][max_index] == 0:
            if random_stock_list[i]['volume'][min_index] == 0:
                min_index += 1
            if random_stock_list[i]['volume'][max_index] == 0:
                max_index -= 1
            if max_index <= min_index:
                break

        while min_index < max_index:
            data = random_stock_list[i][:min_index+1][-max_date-1:]
            if len(data[np.where(data['volume']==0)]) > 0:
                #print "min_index++ %d"%len(data[np.where(data['volume']==0)])
                min_index += 1
            break

        if max_index <= min_index:
            #print "too less data ==================================================="
            #print random_stock_list[i][-history_day-max_date:]
            continue

        #assert min_index <= max_index and min_index >= max_date and len(sample_stock_list[i]) >= max_date
        index = random.randint(min_index, max_index)

        #去掉特殊情况
        #因为公式目的不是预测市场，而是找到超额收益，所以需要保证标签数据（即sample_stock_list[i]['rise'][index]）的无偏性
        #当发现数据有偏时就再次取样，保证大体上是无偏的
        loop_time = 0
        max_loop_time = 3
        while (random_stock_list[i]['rise'][index] > 0.09 or sum_returns * random_stock_list[i]['rise'][index] > 0) and loop_time < max_loop_time:
            index = random.randint(min_index, max_index)
            loop_time += 1

        #取样时去掉停盘的数据
        data = random_stock_list[i][index+1-max_date:index+1]
        if len(data[np.where(data['volume'] == 0)]) > 0:
            #print "stop buy day %d"%len(data[np.where(data['volume'] == 0)])
            #print data[np.where(data['volume'] == 0)]
            continue

        day_index_list.append(index)
        sample_stock_list.append(random_stock_list[i])
        sum_returns += random_stock_list[i]['rise'][index]
        assert day_index_list[-1] >= max_date
        if len(day_index_list) == sample_size:
            break

    assert len(day_index_list) == sample_size
    #print sum_returns
    #todo 以后加入行业标签
    return sample_stock_list, day_index_list

#def get_eval_score_list(sample_stock_list, day_index_list, watch_future_size = 5, deposit_rate = 0.8):
#    return [get_eval_score(sample_stock_list[i], day_index_list[i], watch_future_size, deposit_rate) for i in range(len(sample_stock_list))]

def get_score_list(sample_stock_list, day_index_list, watch_future_size = 5):
    return np.array([[get_score(sample_stock_list[i], day_index_list[i], j) for j in range(1, watch_future_size+1)] for i in range(len(sample_stock_list))])

def get_compare_stock_list(stock_list, day_index_list, compare_stock_dict, max_date):
    cmp_stock_list = list()
    stocktype = np.dtype([
        ('date', 'uint64'), ('open', 'float64'),
        ('high', 'float64'), ('low', 'float64'),
        ('close', 'float64'), ('volume', 'float64'),
        ('vwap', 'float64'), ('rise', 'float64'),
        # ('rf','float64')
    ])
    for i in xrange(len(day_index_list)):
        day_index = day_index_list[i]
        start_index = day_index - max_date
        date = stock_list[i]["date"][start_index:day_index + 1]
        bars = np.array([compare_stock_dict[d] for d in date], stocktype)
        rice_col = bars["rise"]
        rice_col[0] = 0
        rice_col[1:] = (bars['close'][1:] - bars['close'][:-1]) / bars['close'][:-1]
        cmp_stock_list.append(bars)

    return cmp_stock_list

def set_stock_dict(leaf_dict, stock_list, day_index_list, pre_path = "", max_date = 260):
    #start_index = max(day_index - max_date,0)
    open_data = list()
    high_data = list()
    low_data = list()
    close_data = list()
    volume_data = list()
    vwap_data = list()
    returns_data = list()
    for i in xrange(len(day_index_list)):
        day_index = day_index_list[i]
        assert day_index >= max_date
        start_index = day_index - max_date
        open_data.append(stock_list[i]["open"][start_index:day_index+1])
        high_data.append(stock_list[i]["high"][start_index:day_index + 1])
        low_data.append(stock_list[i]["low"][start_index:day_index + 1])
        close_data.append(stock_list[i]["close"][start_index:day_index + 1])
        volume_data.append(stock_list[i]["volume"][start_index:day_index + 1])
        vwap_data.append(stock_list[i]["vwap"][start_index:day_index + 1])
        returns_data.append(stock_list[i]["rise"][start_index:day_index + 1])

    leaf_dict["%sopen"%pre_path] = np.array(open_data).T
    leaf_dict["%shigh"%pre_path] = np.array(high_data).T
    leaf_dict["%slow"%pre_path] = np.array(low_data).T
    leaf_dict["%sclose"%pre_path] = np.array(close_data).T
    leaf_dict["%svolume"%pre_path] = np.array(volume_data).T
    leaf_dict["%svwap"%pre_path] = np.array(vwap_data).T
    leaf_dict["%sreturns"%pre_path] = np.array(returns_data).T

