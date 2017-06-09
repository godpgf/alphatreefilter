#coding=utf-8
#author=godpgf
#作为alphatree和stock data之间的中介
from stdb import *
from stdb.data_reader import date2int
import numpy as np
import random


def get_alphatree_data(sample_stock_list, day_index_list, stock_all, max_date = 520, watch_future_size = 5):
    score_list = get_score_list(sample_stock_list, day_index_list, watch_future_size)
    #real_score_list = get_real_score_list(sample_stock_list, day_index_list, watch_future_size)
    stock_all_dict = {}
    for s in stock_all:
        stock_all_dict[s[0]] = s
    #todo
    leaf_dict_list = list()
    for i in range(len(sample_stock_list)):
        leaf_dict = dict()
        set_stock_dict(leaf_dict, sample_stock_list[i], day_index_list[i], "", max_date)
        comp_stock = get_compare_stock(sample_stock_list[i], day_index_list[i], stock_all_dict, max_date)
        set_comp_stock_dict(leaf_dict, comp_stock, 'IndClass.subindustry:')
        set_comp_stock_dict(leaf_dict, comp_stock, 'IndClass.sector:')
        set_comp_stock_dict(leaf_dict, comp_stock, 'IndClass.industry:')
        leaf_dict['score'] = score_list[i]
        #leaf_dict['real_score'] = real_score_list[i]
        leaf_dict_list.append(leaf_dict)
    return leaf_dict_list

def get_current_alphatree_data(cur_stock_list, cur_code_list, stock_all, max_date):
    #todo
    stock_all_dict = {}
    for s in stock_all:
        stock_all_dict[s[0]] = s
    leaf_dict_list = list()
    for i in range(len(cur_stock_list)):
        leaf_dict = dict()
        set_stock_dict(leaf_dict, cur_stock_list[i], len(cur_stock_list[i]) - 1, "", max_date)
        comp_stock = get_compare_stock(cur_stock_list[i], len(cur_stock_list[i]) - 1, stock_all_dict, max_date)
        set_comp_stock_dict(leaf_dict, comp_stock, 'IndClass.subindustry:')
        set_comp_stock_dict(leaf_dict, comp_stock, 'IndClass.sector:')
        set_comp_stock_dict(leaf_dict, comp_stock, 'IndClass.industry:')
        leaf_dict['code'] = cur_code_list[i]
        leaf_dict_list.append(leaf_dict)
    return leaf_dict_list

#读取近期股票数据
def read_stock_list(cache_path, is_offline, max_date = 260, cur_date = None):
    codeProxy = LocalCodeProxy(cache_path, is_offline)
    dataProxy = LocalDataProxy(cache_path, is_offline)
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
            if len(data) > max_date:
                codeList.append(code)
                stockList.append(data)
    return stockList, codeList, dataProxy.get_all_Data('0000001')

def filter_current_stock_list(stock_list, code_list, stock_all, max_date = 260):
    new_stock_list = []
    new_code_list = []
    for i in xrange(len(stock_list)):
        if stock_list[i]['date'][-1] == stock_all['date'][-1] and len(stock_list[i]) >= max_date:
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
    #score_list = list()
    sample_stock_list = stock_list[:]
    random.shuffle(sample_stock_list)
    sample_stock_list = sample_stock_list[:sample_size]
    for i in xrange(len(sample_stock_list)):
        min_index = max(len(sample_stock_list[i]) - history_day - watch_future_size, max_date)
        max_index = len(sample_stock_list[i]) - 1 - watch_future_size
        assert min_index <= max_index and min_index >= max_date and len(sample_stock_list[i]) >= max_date
        index = random.randint(min_index, max_index)
        #去掉特殊情况
        while sample_stock_list[i]['rise'][index] > 0.09:
            index = random.randint(min_index, max_index)
        day_index_list.append(index)
        assert day_index_list[-1] >= max_date
    #todo 以后加入行业标签
    return sample_stock_list, day_index_list

#def get_eval_score_list(sample_stock_list, day_index_list, watch_future_size = 5, deposit_rate = 0.8):
#    return [get_eval_score(sample_stock_list[i], day_index_list[i], watch_future_size, deposit_rate) for i in range(len(sample_stock_list))]

def get_score_list(sample_stock_list, day_index_list, watch_future_size = 5):
    return np.array([[get_score(sample_stock_list[i], day_index_list[i], j) for j in range(1, watch_future_size+1)] for i in range(len(sample_stock_list))])

def get_compare_stock(stock, day_index, compare_stock_dict, max_date):
    start_index = max(day_index - max_date, 0)
    date = stock["date"][start_index:day_index + 1]
    stocktype = np.dtype([
        ('date', 'uint64'), ('open', 'float64'),
        ('high', 'float64'), ('low', 'float64'),
        ('close', 'float64'), ('volume', 'float64'),
        ('vwap', 'float64'), ('rise', 'float64'),
        # ('rf','float64')
    ])
    bars = np.array([compare_stock_dict[d] for d in date], stocktype)
    rice_col = bars["rise"]
    rice_col[0] = 0
    rice_col[1:] = (bars['close'][1:] - bars['close'][:-1]) / bars['close'][:-1]
    return bars

def set_comp_stock_dict(leaf_dict, c_stock, pre_path = ""):
    leaf_dict["%sopen"%pre_path] = c_stock["open"]
    leaf_dict["%shigh"%pre_path] = c_stock["high"]
    leaf_dict["%slow"%pre_path] = c_stock["low"]
    leaf_dict["%sclose"%pre_path] = c_stock["close"]
    leaf_dict["%svolume"%pre_path] = c_stock["volume"]
    leaf_dict["%svwap"%pre_path] = c_stock["vwap"]
    leaf_dict["%sreturns"%pre_path] = c_stock["rise"]

def set_stock_dict(leaf_dict, stock, day_index, pre_path = "", max_date = 260):
    start_index = max(day_index - max_date,0)
    leaf_dict["%sopen"%pre_path] = stock["open"][start_index:day_index + 1]
    leaf_dict["%shigh"%pre_path] = stock["high"][start_index:day_index + 1]
    leaf_dict["%slow"%pre_path] = stock["low"][start_index:day_index + 1]
    leaf_dict["%sclose"%pre_path] = stock["close"][start_index:day_index + 1]
    leaf_dict["%svolume"%pre_path] = stock["volume"][start_index:day_index + 1]
    leaf_dict["%svwap"%pre_path] = stock["vwap"][start_index:day_index + 1]
    leaf_dict["%sreturns"%pre_path] = stock["rise"][start_index:day_index + 1]
    assert day_index >= 260
    assert len(leaf_dict["%sopen"%pre_path]) >= 260
    assert len(leaf_dict["%shigh" % pre_path]) >= 260
    assert len(leaf_dict["%slow" % pre_path]) >= 260
    assert len(leaf_dict["%sclose" % pre_path]) >= 260
    assert len(leaf_dict["%svolume" % pre_path]) >= 260
    assert len(leaf_dict["%svwap" % pre_path]) >= 260
    assert len(leaf_dict["%sreturns" % pre_path]) >= 260
