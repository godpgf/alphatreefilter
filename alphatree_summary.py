# coding=utf-8
# author=godpgf
from alphatreefilter import *
import datetime
from stdb import *
import pandas as pd
import numpy as np
from alphatree import write_alpha_tree_list

if __name__ == '__main__':
    #1、读出所有alphatree
    alpha_tree = read_alphatree_from_path("doc/alpha_atom.csv", "resources/")

    #2、得到股票数据接口
    cache_path = "test"
    is_offline = True
    codeProxy = LocalCodeProxy(cache_path, is_offline)
    dataProxy = LocalDataProxy(cache_path, is_offline)

    #3、开始总结
    summary_alphatree, sub_alphatree = filter_complex_alpha(alpha_tree, codeProxy, dataProxy)

    #保存
    write_alpha_tree_list('doc/summary_alphatree.txt', summary_alphatree)
    write_alpha_tree_list('doc/summary_sub_alphatree.txt', sub_alphatree, 'SubAlpha#')