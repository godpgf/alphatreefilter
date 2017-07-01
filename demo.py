# coding=utf-8
# author=godpgf
from alphatreefilter import *
import datetime
from stdb import *
import pandas as pd
import numpy as np
from alphatree import write_alpha_tree_list
from portfolio import MaxSharpePortfolio

if __name__ == '__main__':
    #1、读出所有alphatree
    alpha_tree = read_alphatree_from_path("doc/alpha_atom.csv", "resources/")

    #2、得到股票数据接口
    cache_path = "test"
    is_offline = False
    codeProxy = LocalCodeProxy(cache_path, is_offline)
    dataProxy = LocalDataProxy(cache_path, is_offline)

    #3、过滤股票
    alphatree_score_list = filter_stock(alpha_tree, codeProxy, dataProxy)


    #4、存档选择的alphatree
    write_alpha_tree_list('doc/alpha_tree_%s.txt'%get_dt(datetime.datetime.now()), [alphatree_score.alphatree for alphatree_score in alphatree_score_list])

    #5、构建投资组合
    max_stock_num = 5
    if len(alphatree_score_list) > 0:
        stock_list = list()
        score_list = list()
        sharp_list = list()
        day_list = list()
        weight_list = list()
        if len(alphatree_score_list) == 1 and len(alphatree_score_list[0].codes) == 1:
            stock_list.append(alphatree_score_list[0].codes[0])
            score_list.append(alphatree_score_list[0].score)
            sharp_list.append(alphatree_score_list[0].score/alphatree_score_list[0].score_stddev)
            day_list.append(alphatree_score_list[0].hold_day_num)
            weight_list.append(1.0)
        else:
            cur = datetime.datetime.now()
            dt = pd.Timestamp("%d-%d-%d"%(cur.year,cur.month,cur.day))
            msp = MaxSharpePortfolio()
            for alphatree_score in alphatree_score_list:
                for code in alphatree_score.codes:
                    msp.add_stock(code, dataProxy.history(code, dt, 25, '1d','close'), alphatree_score.score / alphatree_score.score_stddev)
                    stock_list.append(code)
                    score_list.append(alphatree_score.score)
                    sharp_list.append(alphatree_score.score / alphatree_score.score_stddev)
                    day_list.append(alphatree_score.hold_day_num)
            weight_list = msp.create()
            sort_index = np.argsort(-weight_list)
            stock_list = [stock_list[index] for index in sort_index]
            score_list = [score_list[index] for index in sort_index]
            sharp_list = [sharp_list[index] for index in sort_index]
            day_list = [day_list[index] for index in sort_index]
            weight_list = [weight_list[index] for index in sort_index]
        #存档选择的stock
        pd.DataFrame({
                'stock': stock_list[:max_stock_num],
                'score': score_list[:max_stock_num],
                'sharp': sharp_list[:max_stock_num],
                'day': day_list[:max_stock_num],
                'weight': np.array(weight_list[:max_stock_num])/np.sum(np.array(weight_list[:max_stock_num])),
            }).to_csv('doc/stock_predict_%s.csv'%get_dt(datetime.datetime.now()), index=False)
    else:
        print "没有满足条件的alphatree"