# coding=utf-8
# author=godpgf
import os
import pandas as pd
import numpy as np
from alphatree import read_alpha_atom_list, read_alpha_tree_list, write_alpha_tree_list
from alphatreefilter import *
import datetime



if __name__ == '__main__':
    #1、读出所有alphatree
    alpha_tree = read_alphatree_from_path("doc/alpha_atom.csv", "resources/")

    #2、读出股票数据
    cache_path = "test"
    is_offline = True
    max_date = 260
    watch_future_size = 5
    stock_list, code_list, stock_market = read_stock_list(cache_path, is_offline, max_date + watch_future_size + 1)

    #3、过滤alphatree，并得到alphatree的分数、持有期、alpha范围
    history_day = 160
    sample_size = 896#960
    last_history_day = 45
    last_sample_size = 1024
    min_scores = [#0.0,
                  0.01, 0.016, 0.018, 0.02]
    focus_percents = [#0.16,
                      0.064, 0.048, 0.032, 0.012]
    leaf_dict_filler = level_sample_history_stock(stock_list, stock_market, watch_future_size, history_day, sample_size, last_history_day, last_sample_size, max_date, len(min_scores))
    alphatree_score_list = filter_alpha_tree(alpha_tree, leaf_dict_filler, min_scores, focus_percents, watch_future_size)

    #3、得到所有满足要求的stock
    leaf_dict_list = filter_current_stock(stock_list, code_list, stock_market, max_date)
    codes_list = [filter_stock_from_alphatree_score(leaf_dict_list, alphatree_score) for alphatree_score in alphatree_score_list]

    last_alphatree_score_list, last_codes_list = list(), list()
    for i in xrange(len(codes_list)):
        if len(codes_list[i]) > 0:
            last_alphatree_score_list.append(alphatree_score_list[i])
            last_codes_list.append(codes_list[i])
    alphatree_score_list, codes_list = last_alphatree_score_list, last_codes_list


    #存档选择的alphatree
    write_alpha_tree_list('doc/alpha_tree_%s.txt'%get_dt(datetime.datetime.now()), [alphatree_score.alphatree for alphatree_score in alphatree_score_list])

    if len(alphatree_score_list) > 0:
        #存档选择的stock
        pd.DataFrame({
            'stock': [','.join(codes) for codes in codes_list],
            'score': [alphatree_score.score for alphatree_score in alphatree_score_list],
            'sharp': [alphatree_score.score / alphatree_score.score_stddev for alphatree_score in alphatree_score_list],
            'day': [alphatree_score.hold_day_num for alphatree_score in alphatree_score_list],
        }).to_csv('doc/stock_predict_%s.csv'%get_dt(datetime.datetime.now()), index=False)
    else:
        print "没有满足条件的alphatree"

