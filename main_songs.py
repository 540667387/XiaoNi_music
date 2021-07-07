"""
@author: xuji0003
@file: main_songs.py
@Description: TODO
@time: 2021/6/15
"""
import config
from source import MusicSource
import os
import sys
from utils import mkdir

__all__ = ["init", "getSongList", "download"]


def getSongList() -> list:
    ms = MusicSource()
    if config.get("keyword"):
        songs_list = ms.search(config.get("keyword"), config.get("source").split())
        return songs_list
    else:
        return []


def init(keyword, pageNo=1, outdir=os.path.join(os.path.dirname(sys.executable), 'songCache')):
    config.init()
    config.set("keyword", keyword)
    config.set("pageNo", pageNo)
    dir_path = mkdir(outdir)
    config.set("outdir", dir_path)


def download(songs_list) -> (list, list, list):
    song_file_list = []
    lyrics_file_list = []
    cover_file_list = []
    for song in songs_list:
        out_song_file, out_lyrics_file, cover_file = downloadSingle(song, cover_flag=False)
        song_file_list.append(out_song_file)
        lyrics_file_list.append(out_lyrics_file)
        cover_file_list.append(cover_file)
    return song_file_list, lyrics_file_list, cover_file_list


def downloadSingle(song, song_flag=True, lyrics_flag=True, cover_flag=True) -> (str, str, str):
    return song.download(song_flag, lyrics_flag, cover_flag)


if __name__ == "__main__":
    init("毛不易", outdir= '.\songCache_test')
    songs_ist = getSongList()
    download(songs_ist[:10])

    print(songs_ist)
    print(len(songs_ist))

