"""
@author: xuji0003
@file: filter_invalid
@Description: TODO
@time: 2021/7/6
"""


def judge_accompany(string, keyword):
    flag = False
    keyword_list = [i for i in ["伴奏"] if i in keyword]
    string_list = [i for i in ["伴奏"] if i in string]
    if keyword_list == [] and string_list != []:
        flag = True
    return flag


def judge_original(string, keyword):
    flag = False
    keyword_list = [i for i in ["原唱","翻自"] if i in keyword]
    string_list = [i for i in ["原唱","翻自"] if i in string]
    if keyword_list == [] and string_list != []:
        flag = True
    return flag

def judge_show(string, keyword):
    flag = False
    keyword_list = [i for i in ["节目"] if i in keyword]
    string_list = [i for i in ["节目"] if i in string]
    if keyword_list == [] and string_list != []:
        flag = True
    return flag


if __name__ == '__main__':
    print(judge_accompany("aaa伴奏","平凡的一天翻自"))