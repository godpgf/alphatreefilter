# coding=utf-8
# author=godpgf
from .alphatree_data_reader import read_stock_list
from .alphatree_filter import level_sample_history_stock, filter_alpha_tree, filter_current_stock, filter_alphatree_score

def filter_stock(alpha_tree, codeProxy, dataProxy,
                 max_date = 260, watch_future_size = 5, cur_date = None,
                 history_day=160, sample_size=896, last_history_day=45, last_sample_size=1024,
                 min_scores = [0.006, 0.01, 0.016, 0.018, 0.018, 0.019], focus_percents = [0.064, 0.048, 0.024, 0.012, 0.012, 0.012], last_level_size = 3
                 ):
    #取样股票数据
    stock_list, code_list, stock_market = read_stock_list(codeProxy, dataProxy, max_date + watch_future_size + 1, cur_date)
    leaf_dict_filler = level_sample_history_stock(stock_list, stock_market, watch_future_size, history_day, sample_size, last_history_day, last_sample_size, max_date, len(min_scores)-last_level_size, last_level_size)

    #过滤alphatree，并得到alphatree的分数、持有期、alpha范围
    alphatree_score_list = filter_alpha_tree(alpha_tree, leaf_dict_filler, min_scores, focus_percents, watch_future_size)

    #得到所有满足要求的stock
    leaf_dict_list = filter_current_stock(stock_list, code_list, stock_market, max_date)
    alphatree_score_list = filter_alphatree_score(leaf_dict_list, alphatree_score_list)

    return alphatree_score_list