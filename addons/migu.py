"""
@author: xuji0003
@file: migu.py
@Description: TODO
@time: 2021/6/15
"""

import copy
import config
from api import MusicApi
from song import BasicSong
from utils import getPageList, filterBadCharacter, sortedDictValues
import threading
from exceptions import DataError
from filter_invalid import *


class MiguApi(MusicApi):
    session = copy.deepcopy(MusicApi.session)
    session.headers.update(
        {"referer": "http://music.migu.cn/", "User-Agent": config.get("ios_useragent")}
    )

    @classmethod
    def song_request(cls, keyword, pageNo):
        params = {
            "ua": "Android_migu",
            "version": "5.0.1",
            "text": keyword,
            "pageNo": pageNo,
            "searchSwitch": '{"song":1,"album":0,"singer":0,"tagSong":0,"mvSong":0,"songlist":0,"bestShow":1}',
        }

        song_res_data = (
            MiguApi.request(
                "http://pd.musicapp.migu.cn/MIGUM2.0/v1.0/content/search_all.do",
                method="GET",
                data=params,
            )
                .get("songResultData", {})
        )
        return song_res_data


class MiguSong(BasicSong):
    def __init__(self):
        super(MiguSong, self).__init__()
        self.content_id = ""


def migu_search(keyword) -> list:
    """ 搜索音乐 """
    pageNo = config.get("pageNo") or 1
    ## 每页固定输出20首歌
    songs_dict = {}
    thread_pool = []

    song_res_data = MiguApi.song_request(keyword=keyword, pageNo=pageNo)
    songCount = int(song_res_data.get("totalCount", "0"))
    print(str(songCount) + "migu")

    try:
        for i in getPageList(songCount, 20):
            t = threading.Thread(
                target=search_thread,
                args=(keyword, i, songs_dict),
            )
            thread_pool.append(t)
            t.start()
        for t in thread_pool:
            t.join()
    except Exception as e:
        raise DataError(e)

    songs_list = sortedDictValues(songs_dict)
    print(str(len(songs_list)) + "去重后migu")
    return songs_list


def search_thread(keyword, pageNo, songs_dict):
    i = 0
    res_data = MiguApi.song_request(keyword=keyword, pageNo=pageNo).get("result", [])
    for item in res_data:
        title = filterBadCharacter(item.get("name", ""))
        if judge_accompany(title, keyword): continue
        if judge_original(title, keyword): continue
        if judge_show(title, keyword): continue
        # 获得歌手名字
        singers = [s.get("name", "") for s in item.get("singers", [])]
        song = MiguSong()
        song.source = "MIGU"
        song.id = item.get("id", "")
        song.title = title
        song.singer = filterBadCharacter("、".join(singers))
        albums = item.get("albums", [])
        song.album = filterBadCharacter(albums[0].get("name", "") if len(albums) else "")
        imgItems = item.get("imgItems", [])
        song.cover_url = imgItems[0].get("img", "") if len(imgItems) else ""
        song.lyrics_url = item.get("lyricUrl", item.get("trcUrl", ""))
        # song.duration = item.get("interval", 0)
        # 特有字段
        song.content_id = item.get("contentId", "")
        # 品质从高到低排序
        rate_list = sorted(
            item.get("rateFormats", []), key=lambda x: int(x["size"]), reverse=True
        )
        for rate in rate_list:
            url = "http://app.pd.nf.migu.cn/MIGUM2.0/v1.0/content/sub/listenSong.do?toneFlag={formatType}&netType=00&userId=15548614588710179085069&ua=Android_migu&version=5.1&copyrightId=0&contentId={contentId}&resourceType={resourceType}&channel=0".format(
                formatType=rate.get("formatType", "SQ"),
                contentId=song.content_id,
                resourceType=rate.get("resourceType", "E"),
            )
            song.song_url = url
            if song.available:
                song.size = round(int(rate.get("size", 0)) / 1048576, 2)
                ext = "flac" if rate.get("formatType", "") == "SQ" else "mp3"
                song.ext = rate.get("fileType", ext)
                break

        songs_dict[pageNo * 20 + i] = song
        i += 1


search = migu_search
