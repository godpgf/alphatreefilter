# coding=utf-8
# author=godpgf
#过滤找出一些子公式
#todo 改成聚合
from .alphatree_filter import get_alphatree_relevance_matrix
from alphatree.parse.alpha_tree_reader import alpha_tree_2_str
from alphatree import AlphaTree, AlphaNode, AlphaAtom
import numpy as np

def cal_contribution(relevance_matrix, ids):
    if len(ids) == 1:
        return 0
    score = 0
    for i in xrange(1,len(ids)):
        max_relevance = 0
        for j in xrange(0,i):
            max_relevance = max(relevance_matrix[ids[j]][ids[i]], max_relevance)
        score += (1.0 - max_relevance)
    return score

def get_sub_alphatree_from_node(node):
    sub_alphatree_list = list()
    if len(node.children) == 0:
        return sub_alphatree_list

    root = AlphaNode(AlphaAtom.create_none_atom())
    root.add_child(node.clone())
    sub_alphatree_list.append(AlphaTree(root))

    for child in node.children:
        sub_alphatree_list.extend(get_sub_alphatree_from_node(child))

    return sub_alphatree_list


def get_sub_alphatree(alphatree, min_depth = 3):
    sub_alphatree_list = get_sub_alphatree_from_node(alphatree.root.children[0])
    new_sub_alphatree_list = list()
    for sub_alphatree in sub_alphatree_list:
        if sub_alphatree.get_depth() >= min_depth:
            new_sub_alphatree_list.append(sub_alphatree)
    return new_sub_alphatree_list

def filter_sub_alphatree(leaf_dict_list, alphatree_list, relevance_day = 25, min_score = 1.0):
    sub_alphatree_list = [get_sub_alphatree(alphatree) for alphatree in alphatree_list]
    sub_alphatree_str_list = list()
    sub_alphatree_num = dict()
    for id, sub_alphatree in enumerate(sub_alphatree_list):
        sub_alphatree_str = list()
        for sat in sub_alphatree:
            str = alpha_tree_2_str(sat)
            sub_alphatree_str.append((str, id))
            if str not in sub_alphatree_num:
                sub_alphatree_num[str] = 0
            sub_alphatree_num[str] = sub_alphatree_num[str] + 1
        sub_alphatree_str_list.append(sub_alphatree_str)

    #过滤没有重复sub_alphatree的alphatree
    choose_alpha_tree = list()
    for i in xrange(len(sub_alphatree_str_list)):
        sub_alphatree_str = sub_alphatree_str_list[i]
        for j in xrange(len(sub_alphatree_str)):
            str, id = sub_alphatree_str[j]
            if sub_alphatree_num[str] > 1:
                print "%s->%d"%(str, sub_alphatree_num[str])
                choose_alpha_tree.append(i)
                break

    alphatree_list = [alphatree_list[i] for i in choose_alpha_tree]
    sub_alphatree_list = [sub_alphatree_list[i] for i in choose_alpha_tree]
    sub_alphatree_str_list = [sub_alphatree_str_list[i] for i in choose_alpha_tree]

    #alphatree的相关性分析，某个sub_tree出现在两个越不相关的alphatree中，贡献越大
    relevance_matrix = get_alphatree_relevance_matrix(leaf_dict_list, alphatree_list, relevance_day)

    #得到子树对应的所有alphatree的id
    same_subtree_dict = dict()
    for i in xrange(len(sub_alphatree_list)):
        for j in xrange(len(sub_alphatree_list[i])):
            str, id = sub_alphatree_str_list[i][j]
            if str not in same_subtree_dict:
                same_subtree_dict[str] = list()
            same_subtree_dict[str].append(id)

    #得到子树得分
    subtree_score_dict = dict()
    for key, value in same_subtree_dict.items():
        subtree_score_dict[key] = cal_contribution(relevance_matrix, value)
        print "contribution %.4f"%subtree_score_dict[key]

    #过滤得到贡献最大的子树
    str_2_new_sub_alphatree = dict()
    for i in xrange(len(sub_alphatree_list)):
        for j in xrange(len(sub_alphatree_list[i])):
            str, id = sub_alphatree_str_list[i][j]
            if subtree_score_dict[str] > min_score and str not in str_2_new_sub_alphatree:
                str_2_new_sub_alphatree[str] = sub_alphatree_list[i][j]

    return [value for key, value in str_2_new_sub_alphatree.items()]