# coding=utf-8
# author=godpgf
import os
import pandas as pd
import numpy as np
from alphatree import read_alpha_atom_list, read_alpha_tree_list, write_alpha_tree_list
from alphatreefilter import *
import datetime

def get_dt(now):
    year = '%d'%now.year
    month = '0%d'%now.month if now.month < 10 else '%d'%now.month
    day = '0%d'%now.day if now.day < 10 else '%d'%now.day
    return '%s%s%s'%(year, month, day)

def get_dt_from_path(path):
    return path.split('_')[-1].split('.')[0]

def read_alphatree_from_path(alpha_atom_path, rootdir = "resources/", from_dt = None, to_dt = None):
    alpha_element = read_alpha_atom_list(alpha_atom_path)
    alpha_tree = list()
    path_list = os.listdir(rootdir)  # 列出文件夹下所有的目录与文件
    for i in range(0, len(path_list)):
        path = os.path.join(rootdir, path_list[i])
        dt = get_dt_from_path(path)
        if from_dt and dt < from_dt:
            continue
        if to_dt and dt > to_dt:
            continue
        if os.path.isfile(path):
            alpha_tree.extend(read_alpha_tree_list(path, alpha_element))
    return alpha_tree


def filter_alpha_tree(alpha_tree, stock_list, stock_marker, watch_future_size, history_day, sample_size, max_date, focus_percent, min_filter_score):
    sample_stock_list, day_index_list = sample_stock(stock_list, watch_future_size, history_day, sample_size, max_date)
    leaf_dict_list = get_alphatree_data(sample_stock_list, day_index_list, stock_marker, max_date * 2, watch_future_size)
    alphatree_score_list = []
    for atree in alpha_tree:
        alphatree_score = get_alpha_tree_score(atree, leaf_dict_list,focus_percent, watch_future_size)
        if alphatree_score.score > min_filter_score:
            alphatree_score_list.append(alphatree_score)
    return alphatree_score_list


def filter_current_stock(stock_list, code_list, stock_market, max_date):
    cur_stock_list, cur_code_list = filter_current_stock_list(stock_list, code_list, stock_market, max_date)
    return get_current_alphatree_data(cur_stock_list, cur_code_list, stock_market, max_date * 2)


def filter_stock_from_alphatree_score(leaf_dict_list, alphatree_score):
    code_list = list()
    alpha_list = list()
    for leaf_dict in leaf_dict_list:
        alpha = alphatree_score.alphatree.get_alpha(leaf_dict)[-1]
        if alpha > alphatree_score.alpha_min:
            code_list.append(leaf_dict['code'][0])
            alpha_list.append(alpha)
    sort_index = np.argsort(-np.array(alpha_list))
    return [code_list[index] for index in sort_index]

