"""
@author: xuji0003
@file: utils.py
@Description: TODO
@time: 2021/6/16
"""

import os
import re
import math


def mkdir(dirName) -> str:
    cur_path = os.path.dirname(os.path.realpath(__file__))  # log_path是存放日志的路径
    path = os.path.join(cur_path, dirName)
    if not os.path.exists(path):
        os.mkdir(path)  # 如果不存在这个logs文件夹，就自动创建一个
    return path


def mkfile(path, fileName):
    full_file = os.path.join(path, fileName)
    if not os.path.exists(full_file):
        open(full_file, 'wb')  # 如果不存在这个文件，就自动创建一个


def get_list_index(collection, ele, default=-1):
    if ele in collection:
        return collection.index(ele)
    else:
        return default


def parseLrc(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lrc_list = f.readlines()
            # 将列表转换为字符串
            strLrc = ''.join(lrc_list)
            # 定义一个存放lrc歌词的空的list
            dictLrc = []
            # 对歌词进行按行切割
            lineListLrc = strLrc.splitlines()
            # 遍历每一行歌词
            for lineLrc in lineListLrc:
                an = re.search('\[\d{2}:\d{2}.\d{2,3}\].+', lineLrc)
                if not an:
                    continue
                # 时间和歌词分开
                listLrc = lineLrc.split("]")
                timeLrc = listLrc[0][1:].split(':')
                # 转换时间格式
                times = float(timeLrc[0]) * 60 + float(timeLrc[1])
                # 把时间当做key，歌词当做value存放在字典中
                # dictLrc[times] = listLrc[1]
                dictLrc.append((times, listLrc[1]))
    except Exception as e:
        print(e)
        dictLrc = []
        dictLrc.append((float(0.0), '暂无歌词'))
        return dictLrc

    return dictLrc


'''清除可能出问题的字符'''


def filterBadCharacter(string):
    need_removed_strs = ['<em>', '</em>', '<', '>', '\\', '/', '?', ':', '"', '：', '|', '？', '*']
    for item in need_removed_strs:
        string = string.replace(item, '')
    try:
        rule = re.compile(u'[\U00010000-\U0010ffff]')
    except:
        rule = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')
    string = rule.sub('', string).replace("（", "(").replace("）", ")")
    return string.strip().encode('utf-8', 'ignore').decode('utf-8')


def getOffsetList(totalCount, limit) -> list:
    l = []
    for i in range(0, math.ceil(totalCount / limit)):
        l.append(i * limit)
    return l


def getPageList(totalCount, number) -> list:
    l = []
    for i in range(0, math.ceil(totalCount / number)):
        l.append(i + 1)
    return l


def sortedDictValues(adict, reverse=False) -> list:
    keys = sorted(adict.keys(), reverse=reverse)
    return [adict[key] for key in keys]


def getPageIndexs(page, page_count):
    page_indexs = []
    for i in range((page - 1) * page_count, page * page_count):
        page_indexs.append(i)
    return page_indexs


if __name__ == '__main__':
    a = parseLrc("songCache/毛不易 - 消愁.lrc")
    for (key, value) in a:
        print(key)
        print(value)
    # getOffsetList(totalCount=100,limit=100)
    # print(getPageList(181, 60))
    # print(judge_accompany("断了的弦", ""))
    # print(getPageIndexs(3, 20))
