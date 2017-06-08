# coding=utf-8
# author=godpgf
import numpy as np
import math

f = open("doc/log.txt", 'w+')
is_debug = True

#快速得到一个alphatree的得分
#def get_alpha_tree_score(alpha_tree, leaf_dict_list, focus_percent):
#    watch_length = int(len(leaf_dict_list) * focus_percent)
#    alpha_list = list()

#    if is_debug:
#        from alphatree.parse.alpha_tree_reader import decode_base_operators,encode_opt_tree
#        print >>f, decode_base_operators(encode_opt_tree(alpha_tree))

#    for leaf_dict in leaf_dict_list:
#        alpha_list.append(alpha_tree.get_alpha(leaf_dict)[-1])

#    sort_index = np.argsort(-np.array(alpha_list))
#    score = 0
#    #debug_str = ''
#    for i in xrange(watch_length):
#        score += leaf_dict_list[sort_index[i]]['score']

#    score /= watch_length


#    alpha_list = np.array(alpha_list)
#    if is_debug:
#        print>>f, alpha_list[sort_index[:watch_length]]
#        #print debug_str
#        print>>f, score
#        print score

#    return score

#精确得到一个alphatree的得分、达到这个得分的alpha范围、持有期
def get_alpha_tree_score(alpha_tree, leaf_dict_list, focus_percent, watch_future_size):
    watch_length = int(len(leaf_dict_list) * focus_percent)
    alpha_list = list()

    if is_debug:
        from alphatree.parse.alpha_tree_reader import decode_base_operators,encode_opt_tree
        print >>f, decode_base_operators(encode_opt_tree(alpha_tree))

    for leaf_dict in leaf_dict_list:
        alpha_list.append(alpha_tree.get_alpha(leaf_dict)[-1])

    sort_index = np.argsort(-np.array(alpha_list))
    score = np.zeros(watch_future_size)

    for i in xrange(watch_length):
        cur_score = leaf_dict_list[sort_index[i]]['score']
        score += cur_score

    max_index = 0
    for i in range(1, watch_future_size):
        if score[i] > score[max_index]:
            max_index = i
    score /= watch_length

    max_score = score[max_index]
    score_stddev = 0
    for i in xrange(watch_length):
        delta = leaf_dict_list[sort_index[i]]['score'][max_index] - max_score
        score_stddev += delta ** 2
    score_stddev /= watch_length
    score_stddev = math.sqrt(score_stddev)

    if is_debug:
        alpha_list = np.array(alpha_list)
        print>>f, alpha_list[sort_index[:watch_length]]
        #print debug_str
        print>>f, score[max_index]
        print score[max_index]

    return max_score, score_stddev, alpha_list[sort_index[watch_length-1]], alpha_list[sort_index[0]], max_index + 1