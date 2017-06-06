# coding=utf-8
# author=godpgf
import os
import pandas as pd
from alphatree import read_alpha_atom_list, read_alpha_tree_list
from alphatreefilter import *

if __name__ == '__main__':
    #1、读出所有alphatree
    alpha_element = read_alpha_atom_list("doc/alpha_atom.csv")

    alpha_tree = list()
    rootdir = "resources/"
    list = os.listdir(rootdir)  # 列出文件夹下所有的目录与文件
    for i in range(0, len(list)):
        path = os.path.join(rootdir, list[i])
        if os.path.isfile(path):
            alpha_tree.extend(read_alpha_tree_list(path, alpha_element))

    #2、过滤alphatree，并得到alphatree的分数、持有期、alpha范围
    cache_path = "test"
    is_offline = True
    max_date = 260
    watch_future_size = 5
    history_day = 60
    sample_size = 1024
    focus_percent = 0.016
    min_filter_score = 0.02
    stock_list, code_list, stock_all = read_stock_list(cache_path, is_offline, max_date + watch_future_size + 1)
    sample_stock_list, day_index_list = sample_stock(stock_list, watch_future_size, history_day, sample_size, max_date)
    leaf_dict_list = get_alphatree_data(sample_stock_list, day_index_list, stock_all, max_date * 2, watch_future_size)
    cur_alphatree_list = []
    for atree in alpha_tree:
        score, alpha_min, alpha_max, hold_day_num = get_alpha_tree_score(atree, leaf_dict_list, focus_percent, watch_future_size)
        if score > min_filter_score:
            cur_alphatree_list.append([atree, score, alpha_min, alpha_max, hold_day_num])

    #3、得到所有满足要求的stock
    cur_stock_list, cur_code_list = filter_current_stock_list(stock_list, code_list, stock_all, max_date)
    leaf_dict_list = get_current_alphatree_data(cur_stock_list, cur_code_list, stock_all, max_date * 2)

    stock_list = []
    score_list = []
    hold_day_list = []
    for atree_des in cur_alphatree_list:
        code_list = []
        atree = atree_des[0]
        score = atree_des[1]
        alpha_min = atree_des[2]
        hold_day_num = atree_des[4]
        for leaf_dict in leaf_dict_list:
            if atree_des[0].get_alpha(leaf_dict)[-1] > alpha_min:
                code_list.append(leaf_dict['code'])
        if len(code_list) > 0:
            stock_list.append(','.join(code_list))
            score_list.append(score)
            hold_day_list.append(hold_day_num)

    #保存结果
    df = pd.DataFrame({
        'stock':stock_list,
        'score':score_list,
        'day':hold_day_list
    })
    df.to_csv('doc/stock_predict.csv', index=False)