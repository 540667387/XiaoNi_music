"""
@author: xuji0003
@file: source.py
@Description: Music source proxy object
@time: 2021/6/15
"""

import logging
import threading
import importlib
import re


class MusicSource:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def search(self, keyword, sources_list) -> list:
        thread_pool = []
        ret_songs_dict = {}
        ret_songs_list = []

        for source_key in sources_list:
            print(source_key)
            t = threading.Thread(
                target=self.search_thread,
                args=(source_key, keyword, ret_songs_dict),
            )
            thread_pool.append(t)
            t.start()

        for t in thread_pool:
            t.join()

        if len(sources_list) == 0:
            raise Exception("配置中没有数据源！！！")
        elif len(sources_list) == 1:
            priority1 = ret_songs_dict.get(sources_list[0], [])
            priority2 = []
            priority3 = []
        elif len(sources_list) == 2:
            priority1 = ret_songs_dict.get(sources_list[0], [])
            priority2 = ret_songs_dict.get(sources_list[1], [])
            priority3 = []
        elif len(sources_list) == 3:
            priority1 = ret_songs_dict.get(sources_list[0], [])
            priority2 = ret_songs_dict.get(sources_list[1], [])
            priority3 = ret_songs_dict.get(sources_list[2], [])
        else:
            raise Exception("目前程序只支持三个数据源！！！")

        priority1, priority2, priority3 = self.distinct_song(priority1, priority2, priority3)
        self.sort_song(priority1, priority2, priority3, ret_songs_list)

        return ret_songs_list

    def search_thread(self, source, keyword, ret_songs_dict):
        try:
            addon = importlib.import_module("addons." + source, __package__)
            ret_songs_dict[source] = addon.search(keyword)
        except Exception as e:
            # 最后一起输出错误信息免得影响搜索结果列表排版
            print(source)
            raise e

    def format_song(self, song):
        singer = song.singer
        title = song.title
        if "Live" not in title:
            title = re.sub(r'\(.+\)', "", title).strip()

        return singer + title

    def distinct_song(self, priority1, priority2, priority3) -> (list, list, list):
        if len(priority1) > 100 or len(priority2) > 100 or len(priority3) > 100:
            if len(priority1) <= 100: priority1 = []
            if len(priority2) <= 100: priority2 = []
            if len(priority3) <= 100: priority3 = []

        priority1_keys = list(map(self.format_song, priority1))
        priority1_dict = dict(zip(priority1_keys, priority1))
        priority1_set = list(set(priority1_keys))
        priority1_set.sort(key=priority1_keys.index)

        priority2_keys = list(map(self.format_song, priority2))
        priority2_dict = dict(zip(priority2_keys, priority2))
        priority2_set = list(set(priority2_keys))
        priority2_set.sort(key=priority2_keys.index)

        priority3_keys = list(map(self.format_song, priority3))
        priority3_dict = dict(zip(priority3_keys, priority3))
        priority3_set = list(set(priority3_keys))
        priority3_set.sort(key=priority3_keys.index)

        for k1 in priority1_set:
            for l1 in priority1_set:
                priority1_k1 = re.sub(r'\(.+\)', "", k1).strip()
                priority1_l1 = re.sub(r'\(.+\)', "", l1).strip()
                if priority1_k1 == priority1_l1:
                    if "Live" not in k1 and "Live" in l1:
                        priority1_set.remove(l1)

        for k2 in priority2_set:
            for l2 in priority2_set:
                priority2_k2 = re.sub(r'\(.+\)', "", k2).strip()
                priority2_l2 = re.sub(r'\(.+\)', "", l2).strip()
                if priority2_k2 == priority2_l2:
                    if "Live" not in k2 and "Live" in l2:
                        priority2_set.remove(l2)

        for k3 in priority3_set:
            for l3 in priority3_set:
                priority3_k3 = re.sub(r'\(.+\)', "", k3).strip()
                priority3_l3 = re.sub(r'\(.+\)', "", l3).strip()
                if priority3_k3 == priority3_l3:
                    if "Live" not in k3 and "Live" in l3:
                        priority3_set.remove(l3)

        for i1 in priority1_set:
            for j1 in priority2_set:
                priority2_temp = re.sub(r'\(.+\)', "", j1).strip()
                priority1_temp = re.sub(r'\(.+\)', "", i1).strip()
                if priority2_temp == priority1_temp:
                    if "Live" in i1 and "Live" not in j1:
                        priority1_set.remove(i1)
                    else:
                        if j1 in priority3_set:
                            priority3_set.remove(j1)

        for i2 in priority1_set:
            for j2 in priority3_set:
                priority3_temp = re.sub(r'\(.+\)', "", j2).strip()
                priority1_temp = re.sub(r'\(.+\)', "", i2).strip()
                if priority3_temp == priority1_temp:
                    if "Live" in i2 and "Live" not in j2:
                        priority1_set.remove(i2)
                    else:
                        if j2 in priority3_set:
                            priority3_set.remove(j2)

        for i3 in priority2_set:
            for j3 in priority3_set:
                priority3_temp = re.sub(r'\(.+\)', "", j3).strip()
                priority2_temp = re.sub(r'\(.+\)', "", i3).strip()
                if priority3_temp == priority2_temp:
                    if "Live" in i3 and "Live" not in j3:
                        priority2_set.remove(i3)
                    else:
                        if j3 in priority3_set:
                            priority3_set.remove(j3)

        priority1 = [priority1_dict[x] for x in priority1_set]
        priority2 = [priority2_dict[x] for x in priority2_set]
        priority3 = [priority3_dict[x] for x in priority3_set]

        return priority1, priority2, priority3

    def sort_song(self, priority1, priority2, priority3, ret_songs_list: list):
        max_length = max([len(priority1), len(priority2), len(priority3)])
        for i in range(0, max_length)[::2]:
            if len(priority1) > i: ret_songs_list.append(priority1[i])
            if len(priority1) > (i + 1): ret_songs_list.append(priority1[i + 1])
            if len(priority2) > i: ret_songs_list.append(priority2[i])
            if len(priority2) > (i + 1): ret_songs_list.append(priority2[i + 1])
            if len(priority3) > i: ret_songs_list.append(priority3[i])
            if len(priority3) > (i + 1): ret_songs_list.append(priority3[i + 1])
