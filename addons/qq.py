"""
@author: xuji0003
@file: qq
@Description: TODO
@time: 2021/6/30
"""

import random
import base64
import copy
from api import MusicApi
from song import BasicSong
import json
from utils import filterBadCharacter, getPageList, sortedDictValues
import threading
from exceptions import DataError
from filter_invalid import *

__all__ = ["search"]


class QQApi(MusicApi):
    session = copy.deepcopy(MusicApi.session)
    session.headers.update(
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
            'Referer': 'http://y.qq.com'
        }
    )

    @classmethod
    def song_request(cls, keyword, pageNo, number):
        params = {"w": keyword, "format": "json", "p": pageNo, "n": number}
        result = QQApi.request(
            "https://c.y.qq.com/soso/fcgi-bin/client_search_cp",
            method="GET",
            data=params,
        ).get("data", {}).get("song", {})
        return result


class QQSong(BasicSong):
    def __init__(self):
        super(QQSong, self).__init__()
        self.mid = ""

    def download_lyrics(self):
        url = "https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg"
        params = {
            'songmid': self.mid,
            'g_tk': '5381',
            'loginUin': '0',
            'hostUin': '0',
            'format': 'json',
            'inCharset': 'utf8',
            'outCharset': 'utf-8',
            'platform': 'yqq'
        }

        QQApi.session.headers.update(
            {
                'Referer': 'https://y.qq.com/portal/player.html'
            }
        )

        res_data = QQApi.request(
            url,
            method="GET",
            data=params,
        )
        lyric = res_data.get("lyric", "")
        self.lyrics_text = base64.b64decode(lyric).decode("utf-8")
        out_lyrics_file = ''
        if self.lyrics_text:
            out_lyrics_file = super(QQSong, self)._save_lyrics_text()
        return out_lyrics_file


def qq_search(keyword) -> list:
    """ 搜索音乐 """
    number = 60
    pageNo = 1

    thread_pool = []
    songs_dict = {}

    songCount = QQApi.song_request(
        keyword=keyword, pageNo=pageNo, number=number
    ).get("totalnum", 0)
    print(str(songCount) + "qq")

    try:
        for i in getPageList(songCount, number):
            t = threading.Thread(
                target=search_thread,
                args=(keyword, i, number, songs_dict),
            )
            thread_pool.append(t)
            t.start()
        for t in thread_pool:
            t.join()
    except Exception as e:
        raise DataError(e)

    songs_list = sortedDictValues(songs_dict)
    print(str(len(songs_list)) + "去重后qq")

    return songs_list


def search_thread(keyword, pageNo, number, songs_dict):
    i = 0
    res_data = QQApi.song_request(
        keyword=keyword, pageNo=pageNo, number=number
    ).get("list", [])

    QQApi.session.headers.update(
        {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1',
            'Referer': 'http://y.qq.com'
        }
    )
    for item in res_data:
        title = filterBadCharacter(item.get("songname", ""))
        if judge_accompany(title, keyword): continue
        if judge_original(title, keyword): continue
        if judge_show(title, keyword): continue
        params = {
            'guid': str(random.randrange(1000000000, 10000000000)),
            'loginUin': '3051522991',
            'format': 'json',
            'platform': 'yqq',
            'cid': '205361747',
            'uin': '3051522991',
            'songmid': item['songmid'],
            'needNewCode': '0'
        }
        ext = ''
        filesize = ''
        download_url = ''
        for quality in [("A000", "ape", 800), ("F000", "flac", 800), ("M800", "mp3", 320), ("C400", "m4a", 128),
                        ("M500", "mp3", 128)]:
            params['filename'] = '%s%s.%s' % (quality[0], item['songmid'], quality[1])

            response_json = QQApi.request(
                "https://c.y.qq.com/base/fcgi-bin/fcg_music_express_mobile3.fcg",
                method="GET",
                data=params
            )
            if response_json['code'] != 0: continue
            vkey = response_json.get('data', {}).get('items', [{}])[0].get('vkey', '')
            if vkey:
                ext = quality[1]
                download_url = 'http://dl.stream.qqmusic.qq.com/{}?vkey={}&guid={}&uin=3051522991&fromtag=64'.format(
                    '%s%s.%s' % (quality[0], item['songmid'], quality[1]), vkey, params['guid'])

                if ext in ['ape', 'flac']:
                    filesize = item['size%s' % ext]
                elif ext in ['mp3', 'm4a']:
                    filesize = item['size%s' % quality[-1]]
                break

        if not download_url:
            params = {
                'data': json.dumps({
                    "req": {"module": "CDN.SrfCdnDispatchServer", "method": "GetCdnDispatch",
                            "param": {"guid": "3982823384", "calltype": 0, "userip": ""}},
                    "req_0": {"module": "vkey.GetVkeyServer", "method": "CgiGetVkey",
                              "param": {"guid": "3982823384", "songmid": [item['songmid']], "songtype": [0], "uin": "0",
                                        "loginflag": 1, "platform": "20"}},
                    "comm": {"uin": 0, "format": "json", "ct": 24, "cv": 0}
                })
            }

            response_json = QQApi.request(
                "https://u.y.qq.com/cgi-bin/musicu.fcg",
                method="GET",
                data=params
            )

            if response_json['code'] == 0 and response_json['req']['code'] == 0 and response_json['req_0']['code'] == 0:
                ext = 'm4a'
                download_url = str(response_json["req"]["data"]["freeflowsip"][0]) + str(
                    response_json["req_0"]["data"]["midurlinfo"][0]["purl"])
                filesize = item['size128']
        if (not download_url) or (filesize == '') or (filesize == 0) or (not response_json["req_0"]["data"]["midurlinfo"][0]["purl"]): continue
        # 获得歌手名字
        singers = [s.get("name", "") for s in item.get("singer", "")]
        song = QQSong()
        song.source = "QQ"
        song.id = item.get("songid", "")
        song.title = title
        song.singer = filterBadCharacter("、".join(singers))
        song.album = filterBadCharacter(item.get("albumname", ""))
        song.duration = int(item.get('interval', 0))
        song.size = round(filesize / 1048576, 2)
        song.ext = ext
        song.song_url = download_url
        # 特有字段
        song.mid = item.get("songmid", "")

        songs_dict[pageNo * number + i] = song
        i += 1


search = qq_search
