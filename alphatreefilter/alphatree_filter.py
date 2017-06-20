# coding=utf-8
# author=godpgf
import os
import numpy as np
from alphatree import read_alpha_atom_list, read_alpha_tree_list, write_alpha_tree_list
from alphatreefilter import *
from scipy.stats import pearsonr
from .alphatree_eval import get_alpha_tree_score
import math

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

#取样level_size个tree_leaf_list，从小到大排量，以便后面对alphatree做考核
def level_sample_history_stock(stock_list, stock_marker, watch_future_size = 5, history_day = 160, sample_size = 960, last_history_day = 45, last_sample_size = 1024, max_date = 260, level_size = 3, last_level_size = 3):
    sample_stock_list, day_index_list = sample_stock(stock_list, watch_future_size, history_day, sample_size, max_date)
    leaf_dict_list = get_alphatree_data(sample_stock_list, day_index_list, stock_marker, max_date * 2, watch_future_size)

    min_sample_size = sample_size / (2 ** level_size - 1)

    # 添加各个等级股票数据验证漏斗，特殊处理最后的漏斗数据（最严格，并且重新取样了）
    leaf_dict_filler = list()
    for i in range(level_size):
        leaf_dict_filler.append(
            leaf_dict_list[max(0, 2 ** i - 1) * min_sample_size:((2 ** (i + 1) - 1) * min_sample_size)])
    for i in range(last_level_size):
        last_sample_stock_list, last_day_index_list = sample_stock(stock_list, watch_future_size, last_history_day,
                                                                   last_sample_size, max_date)
        last_leaf_dict_list = get_alphatree_data(last_sample_stock_list, last_day_index_list, stock_marker,
                                                 max_date * 2, watch_future_size)
        leaf_dict_filler.append(last_leaf_dict_list)
    return leaf_dict_filler

def filter_alpha_tree(alpha_tree, leaf_dict_list, min_scores = [0.006, 0.01, 0.016, 0.018, 0.019, 0.02], focus_percents = [0.064, 0.048, 0.024, 0.012, 0.012, 0.012], watch_future_size = 5):
    alphatree_score_list = []
    for atree in alpha_tree:
        alphatree_score = get_alpha_tree_score(atree, leaf_dict_list, min_scores, focus_percents, watch_future_size)

        if alphatree_score.score > min_scores[-1]:
            alphatree_score_list.append(alphatree_score)
    return alphatree_score_list


def filter_current_stock(stock_list, code_list, stock_market, max_date):
    cur_stock_list, cur_code_list = filter_current_stock_list(stock_list, code_list, stock_market, max_date)
    return get_current_alphatree_data(cur_stock_list, cur_code_list, stock_market, max_date * 2)


def get_alphatree_relevance_matrix(leaf_dict_list, alphatree_list, relevance_day = 25):
    distinct_list = list()
    relevance_matrix = [[0.0] * len(alphatree_list)] * len(alphatree_list)
    for alphatree in alphatree_list:
        distinct = list()
        for leaf_dict in leaf_dict_list:
            alpha = alphatree.get_alpha(leaf_dict)
            distinct.append(alpha[max(len(alpha) - relevance_day, 0):])
        distinct_list.append(distinct)

    for i in xrange(len(alphatree_list) - 1):
        for j in xrange(i + 1, len(alphatree_list)):
            relevance = 0
            for k in xrange(len(leaf_dict_list)):
                l = len(distinct_list[i][k])
                r = len(distinct_list[j][k])
                min_len = min(l, r)
                l = distinct_list[i][k][l-min_len:]
                r = distinct_list[j][k][r - min_len:]
                r, p = pearsonr(l, r)
                relevance += 0 if math.isnan(r) else r
            relevance /= len(leaf_dict_list)
            relevance_matrix[i][j] = relevance
            relevance_matrix[j][i] = relevance

    return np.array(relevance_matrix)


def filter_alphatree_score(leaf_dict_list, alphatree_score_list, max_relevance = 0.36, relevance_day = 25):
    new_alphatree_score_list = list()
    #通过得出的股票数量过滤alphatree
    for alphatree_score in alphatree_score_list:
        code_list = list()
        alpha_list = list()
        for leaf_dict in leaf_dict_list:
            alpha = alphatree_score.alphatree.get_alpha(leaf_dict)
            if alpha[-1] >= alphatree_score.alpha_min:
                code_list.append(leaf_dict['code'][0])
                alpha_list.append(alpha[-1])
        sort_index = np.argsort(-np.array(alpha_list))
        alphatree_score.codes = [code_list[index] for index in sort_index]
        if len(alphatree_score.codes) > 0:
            new_alphatree_score_list.append(alphatree_score)

    if len(new_alphatree_score_list) == 0:
        return []
    #通过相关度过滤
    new_alphatree_score_list = sorted(new_alphatree_score_list, key=lambda alphatree_score: alphatree_score.score / alphatree_score.score_stddev)
    relevance_matrix = get_alphatree_relevance_matrix(leaf_dict_list, [alphatree_score.alphatree for alphatree_score in new_alphatree_score_list], relevance_day)

    choose_index = [0]
    for i in xrange(1, len(new_alphatree_score_list)):
        has_relevance_tree = False
        for index in choose_index:
            if relevance_matrix[i][index] > max_relevance:
                has_relevance_tree = True
                break
        if has_relevance_tree is False:
            choose_index.append(i)

    return [new_alphatree_score_list[index] for index in choose_index]

