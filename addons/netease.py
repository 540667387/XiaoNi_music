"""
@author: xuji0003
@file: netease.py
@Description: TODO
@time: 2021/6/29
"""

import os
import binascii
import base64
import json
import copy
from Crypto.Cipher import AES
from api import MusicApi
from exceptions import DataError
from song import BasicSong
from utils import filterBadCharacter, getOffsetList, sortedDictValues
import threading
from filter_invalid import *

__all__ = ["search"]


class NeteaseApi(MusicApi):
    """ Netease music api http://music.163.com """

    session = copy.deepcopy(MusicApi.session)
    session.headers.update({"referer": "http://music.163.com/"})

    @classmethod
    def encode_netease_data(cls, data) -> str:
        data = json.dumps(data)
        key = binascii.unhexlify("7246674226682325323F5E6544673A51")
        encryptor = AES.new(key, AES.MODE_ECB)
        # 补足data长度，使其是16的倍数
        pad = 16 - len(data) % 16
        fix = chr(pad) * pad
        byte_data = (data + fix).encode("utf-8")
        return binascii.hexlify(encryptor.encrypt(byte_data)).upper().decode()

    @classmethod
    def encrypted_request(cls, data) -> dict:
        MODULUS = (
            "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7"
            "b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280"
            "104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932"
            "575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b"
            "3ece0462db0a22b8e7"
        )
        PUBKEY = "010001"
        NONCE = b"0CoJUm6Qyw8W8jud"
        data = json.dumps(data).encode("utf-8")
        secret = cls.create_key(16)
        params = cls.aes(cls.aes(data, NONCE), secret)
        encseckey = cls.rsa(secret, PUBKEY, MODULUS)
        return {"params": params, "encSecKey": encseckey}

    @classmethod
    def aes(cls, text, key):
        pad = 16 - len(text) % 16
        text = text + bytearray([pad] * pad)
        encryptor = AES.new(key, 2, b"0102030405060708")
        ciphertext = encryptor.encrypt(text)
        return base64.b64encode(ciphertext)

    @classmethod
    def rsa(cls, text, pubkey, modulus):
        text = text[::-1]
        rs = pow(int(binascii.hexlify(text), 16), int(pubkey, 16), int(modulus, 16))
        return format(rs, "x").zfill(256)

    @classmethod
    def create_key(cls, size):
        return binascii.hexlify(os.urandom(size))[:16]

    @classmethod
    def song_request(cls, keyword, offset, number):
        eparams = {
            "method": "POST",
            "url": "http://music.163.com/api/cloudsearch/pc",
            "params": {"s": keyword, "type": 1, "offset": offset, "limit": number},
        }
        data = {"eparams": NeteaseApi.encode_netease_data(eparams)}
        result = NeteaseApi.request(
            "http://music.163.com/api/linux/forward", method="POST", data=data
        ).get("result", {})
        return result


class NeteaseSong(BasicSong):
    def __init__(self):
        super(NeteaseSong, self).__init__()

    def download_lyrics(self):
        row_data = {"csrf_token": "", "id": self.id, "lv": -1, "tv": -1}
        data = NeteaseApi.encrypted_request(row_data)

        self.lyrics_text = (
            NeteaseApi.request(
                "https://music.163.com/weapi/song/lyric", method="POST", data=data
            )
                .get("lrc", {})
                .get("lyric", "")
        )
        out_lyrics_file = ''
        if self.lyrics_text:
            out_lyrics_file = super(NeteaseSong, self)._save_lyrics_text()
        return out_lyrics_file


def netease_search(keyword) -> list:
    """ Search song from netease music """
    number = 100
    offset = 0

    songs_dict = {}
    thread_pool = []

    songCount = NeteaseApi.song_request(
        keyword=keyword, offset=offset, number=number
    ).get("songCount", 0)
    print(str(songCount) + "netease")
    try:
        for i in getOffsetList(songCount, number):
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
    print(str(len(songs_list)) + "去重后netease")

    return songs_list


def search_thread(keyword, offset, number, songs_dict):
    global response_json
    i = 0
    try:
        res_data = (
            NeteaseApi.song_request(
                keyword=keyword, offset=offset, number=number
            ).get("songs", {})
        )

        for item in res_data:
            if item.get("privilege", {}).get("fl", {}) == 0: continue  # 没有版权
            title = filterBadCharacter(item.get("name", ""))
            if judge_accompany(title, keyword): continue
            if judge_original(title, keyword): continue
            if judge_show(title, keyword): continue
            # 获得歌手名字
            singers = [s.get("name", "") for s in item.get("ar", [])]
            for q in ['h', 'm', 'l']:
                if item[q] is None: continue
                data = NeteaseApi.encrypted_request({"ids":[item['id']],"level":"standard","encodeType":"aac","csrf_token":""})
                response_json = NeteaseApi.request(
                    "https://music.163.com/weapi/song/enhance/player/url/v1?csrf_token=",
                    method="POST",
                    data=data,
                )
                if response_json.get('code') == 200: break
            if response_json.get('code') != 200: continue
            if "/ymusic/" in response_json['data'][0]['url']:continue
            download_url = response_json['data'][0]['url']
            if not download_url: continue
            song = NeteaseSong()
            song.source = "NETEASE"
            song.id = item.get("id", "")
            song.title = title
            song.singer = filterBadCharacter("、".join(singers))
            song.album = filterBadCharacter(item.get("al", {}).get("name", ""))
            song.duration = int(item.get("dt", 0) / 1000)
            song.size = round(item[q]['size'] / 1048576, 2)
            song.cover_url = item.get("al", {}).get("picUrl", "")
            song.ext = download_url.split('.')[-1]
            song.song_url = download_url
            songs_dict[offset + i] = song
            i += 1
    except Exception as e:
        raise DataError(e)


search = netease_search
