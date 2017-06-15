# coding=utf-8
# author=godpgf
from alphatreefilter import *
import datetime
from stdb import *
import pandas as pd
from alphatree import write_alpha_tree_list

if __name__ == '__main__':
    #1、读出所有alphatree
    alpha_tree = read_alphatree_from_path("doc/alpha_atom.csv", "resources/")

    #2、得到股票数据接口
    cache_path = "test"
    is_offline = True
    codeProxy = LocalCodeProxy(cache_path, is_offline)
    dataProxy = LocalDataProxy(cache_path, is_offline)

    #3、过滤股票
    alphatree_score_list = filter_stock(alpha_tree, codeProxy, dataProxy)


    #4、存档选择的alphatree
    write_alpha_tree_list('doc/alpha_tree_%s.txt'%get_dt(datetime.datetime.now()), [alphatree_score.alphatree for alphatree_score in alphatree_score_list])

    if len(alphatree_score_list) > 0:
        #存档选择的stock
        pd.DataFrame({
            'stock': [','.join(codes) for codes in [alphatree_score.codes for alphatree_score in alphatree_score_list]],
            'score': [alphatree_score.score for alphatree_score in alphatree_score_list],
            'sharp': [alphatree_score.score / alphatree_score.score_stddev for alphatree_score in alphatree_score_list],
            'day': [alphatree_score.hold_day_num for alphatree_score in alphatree_score_list],
        }).to_csv('doc/stock_predict_%s.csv'%get_dt(datetime.datetime.now()), index=False)
    else:
        print "没有满足条件的alphatree"