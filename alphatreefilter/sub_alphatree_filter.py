# coding=utf-8
# author=godpgf
#过滤找出一些子公式
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

def replace_sub_alphatree_from_node(node, str_2_id):
    root = AlphaNode(AlphaAtom.create_none_atom())
    root.add_child(node.clone())
    new_alphatree = AlphaTree(root)
    str = alpha_tree_2_str(new_alphatree)
    if str in str_2_id:
        id = str_2_id[str]
        node.replace_to(AlphaNode(AlphaAtom("SubAlpha#%d"%id)))
    else:
        for child in node.children:
            replace_sub_alphatree_from_node(child, str_2_id)


def replace_sub_alphatree(alphatree, str_2_id):
    replace_sub_alphatree_from_node(alphatree.root.children[0], str_2_id)

def filter_sub_alphatree(leaf_dict, alphatree_list, relevance_day = 25, min_score = 1.0):
    #所有树对应的所有子树
    sub_alphatree_list = [get_sub_alphatree(alphatree) for alphatree in alphatree_list]
    #所有树对应所有子树的字符串表示
    sub_alphatree_str_list = [[alpha_tree_2_str(sat) for sat in sub_alphatree] for sub_alphatree in sub_alphatree_list]


    #子树对应的数量
    sub_alphatree_num = dict()
    for sub_alphatree in sub_alphatree_str_list:
        for str in sub_alphatree:
            if str not in sub_alphatree_num:
                sub_alphatree_num[str] = 0
            sub_alphatree_num[str] = sub_alphatree_num[str] + 1

    #某树中某个子树在其他书中也出现过，就留下它
    choose_alpha_tree_id = list()
    for i in xrange(len(sub_alphatree_str_list)):
        sub_alphatree_str = sub_alphatree_str_list[i]
        for str in sub_alphatree_str:
            if sub_alphatree_num[str] > 1:
                print "%s->%d"%(str, sub_alphatree_num[str])
                choose_alpha_tree_id.append(i)
                break

    choose_alphatree_list = [alphatree_list[i] for i in choose_alpha_tree_id]
    sub_alphatree_list = [sub_alphatree_list[i] for i in choose_alpha_tree_id]
    sub_alphatree_str_list = [sub_alphatree_str_list[i] for i in choose_alpha_tree_id]

    str_2_sub_alphatree = dict()
    for i in xrange(len(sub_alphatree_str_list)):
        for j,str in enumerate(sub_alphatree_str_list[i]):
            if str not in str_2_sub_alphatree:
                str_2_sub_alphatree[str] = sub_alphatree_list[i][j]

    #alphatree的相关性分析，某个sub_tree出现在两个越不相关的alphatree中，贡献越大
    relevance_matrix = get_alphatree_relevance_matrix(leaf_dict, choose_alphatree_list, relevance_day)

    #将子树字符串和所有原树id做映射，以便计算它的贡献度
    same_subtree_dict = dict()
    for i in xrange(len(sub_alphatree_str_list)):
        for str in sub_alphatree_str_list[i]:
            if str not in same_subtree_dict:
                same_subtree_dict[str] = list()
            same_subtree_dict[str].append(i)

    #得到子树得分
    subtree_score_dict = dict()
    for key, value in same_subtree_dict.items():
        subtree_score_dict[key] = cal_contribution(relevance_matrix, value)
        print "contribution %.4f"%subtree_score_dict[key]

    #过滤得到贡献最大的子树
    str_2_new_sub_alphatree = dict()
    for i in xrange(len(sub_alphatree_str_list)):
        for str in sub_alphatree_str_list[i]:
            if subtree_score_dict[str] > min_score and str not in str_2_new_sub_alphatree:
                str_2_new_sub_alphatree[str] = str_2_sub_alphatree[str]

    #建立映射
    str_2_id = dict()
    sub_alphatree_list = list()
    cur_id = 1
    for key, value in str_2_new_sub_alphatree.items():
        str_2_id[key] = cur_id
        sub_alphatree_list.append(value)
        cur_id += 1

    #得到替换子树的tree
    new_alphatree_list = list()
    for i in xrange(len(choose_alphatree_list)):
        choose_tree = True
        for j in xrange(i):
            if abs(relevance_matrix[i][j]) > 0.99:
                choose_tree = False
                break
        if choose_tree:
            new_alphatree = alphatree_list[i].clone()
            replace_sub_alphatree(new_alphatree, str_2_id)
            new_alphatree_list.append(new_alphatree)

    for i in xrange(len(alphatree_list)):
        if i not in choose_alpha_tree_id:
            new_alphatree_list.append(alphatree_list[i])

    return new_alphatree_list, sub_alphatree_list