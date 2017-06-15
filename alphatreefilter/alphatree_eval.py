# coding=utf-8
# author=godpgf
import numpy as np
import math

f = open("doc/log.txt", 'w+')
is_debug = True

class AlphatreeScore(object):
    def __init__(self, alphatree, score, score_stddev = 0, alpha_min = 0, alpha_max = 0, hold_day_num = 0):
        #选中的alphatree
        self.alphatree = alphatree
        #选中alphatree统计到的得分
        self.score = score
        #选择alphatree统计到的得分标准差
        self.score_stddev = score_stddev
        #统计到的最小过滤alpha值
        self.alpha_min = alpha_min
        #统计到的最大过滤alpha值
        self.alpha_max = alpha_max
        #统计到的持有期
        self.hold_day_num = hold_day_num

        self.codes = list()
        self.distinct = list()

#精确得到一个alphatree的得分、达到这个得分的alpha范围、持有期（考核alphatree是分级的，某一级得分太低将不能进入下一级，以提高速度）
def get_alpha_tree_score(alpha_tree, leaf_dict_list, min_scores = [0.01, 0.016, 0.018, 0.02], focus_percents = [0.064, 0.048, 0.032, 0.012], watch_future_size = 5):
    if is_debug:
        from alphatree.parse.alpha_tree_reader import decode_base_operators, encode_opt_tree
        print >> f, decode_base_operators(encode_opt_tree(alpha_tree))
    for i in range(len(min_scores)):

        watch_length = int(len(leaf_dict_list[i]) * focus_percents[i])
        alpha_list = [alpha_tree.get_alpha(leaf_dict)[-1] for leaf_dict in leaf_dict_list[i]]
        sort_index = np.argsort(-np.array(alpha_list))
        score = np.zeros(watch_future_size)

        stock_size = 0
        for j in xrange(len(sort_index)):
            if j < watch_length or abs(alpha_list[sort_index[j]] - alpha_list[sort_index[0]]) < 0.00001:
                cur_score = leaf_dict_list[i][sort_index[j]]['score']
                score += cur_score
                stock_size += 1

        max_index = 0
        for j in range(1, watch_future_size):
            if score[j] > score[max_index]:
                max_index = j
        score /= stock_size
        max_score = score[max_index]

        if is_debug:
            alpha_list = np.array(alpha_list)
            print>>f, alpha_list[sort_index[:stock_size]]
            #print debug_str
            print>>f, score[max_index]
            print "level:%d %.4f (%.4f %.4f) size=%d"%(i, score[max_index],alpha_list[sort_index[stock_size-1]],alpha_list[sort_index[0]],stock_size)

        #在某次考核中失败，将终止
        if max_score < min_scores[i]:
            return AlphatreeScore(alpha_tree, max_score)


        if i == len(min_scores) -1:
            #所有考核都成功
            score_stddev = 0
            for j in xrange(stock_size):
                delta = leaf_dict_list[i][sort_index[j]]['score'][max_index] - max_score
                score_stddev += delta ** 2
            score_stddev /= stock_size
            score_stddev = math.sqrt(score_stddev)

            return AlphatreeScore(alpha_tree, max_score, score_stddev, alpha_list[sort_index[stock_size-1]], alpha_list[sort_index[0]], max_index + 1)
    return None