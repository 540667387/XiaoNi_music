"""
@author: xuji0003
@file: song.py
@Description: TODO
@time: 2021/6/15
"""

import logging
import requests
import datetime
import config
import re
import os


class BasicSong:
    """
        Define the basic properties and methods of a song.
        Such as title, name, singer etc.
    """

    def __init__(self):
        self.idx = 0
        self.id = 0
        self._title = ""
        self._singer = ""
        self.ext = "mp3"
        self.album = ""
        self.size = ""
        self.rate = ""
        self._duration = ""
        self.source = ""
        self._song_url = ""
        # self.song_file = ""
        self.cover_url = ""
        # self.cover_file = ""
        self.lyrics_url = ""
        self.lyrics_text = ""
        # self.lyrics_file = ""
        self._fullname = ""
        self.logger = logging.getLogger(__name__)

    def __repr__(self):
        """ Abstract of the song """
        return "%s-%s-%s %s" % (
            self.title,
            self.singer,
            self.album,
            self.source.upper()
        )

    @property
    def available(self) -> bool:
        """ Not available when url is none or size equal 0 """
        return bool(self.song_url and self.size)

    @property
    def name(self) -> str:
        """ Song file name """
        return "%s - %s.%s" % (self.singer, self.title, self.ext)

    @property
    def duration(self):
        """ 持续时间 H:M:S """
        return self._duration

    @duration.setter
    def duration(self, seconds):
        self._duration = str(datetime.timedelta(seconds=int(seconds)))

    @property
    def song_url(self) -> str:
        return self._song_url

    @song_url.setter
    def song_url(self, url):
        """ Set song url and update size. """
        try:
            r = requests.get(
                url,
                stream=True,
                headers=config.get("wget_headers")
            )
            self._song_url = url
            size = int(r.headers.get("Content-Length", 0))
            # 转换成MB并保留两位小数
            self.size = round(size / 1048576, 2)
            # 设置完整的文件名（不含后缀）
            if not self._fullname:
                self._set_fullname()
        except Exception as e:
            self.logger.info("Request failed: {url}".format(url=url))
            self.logger.info(e)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        value = re.sub(r'[\\/:*?"<>|]', "", value)
        self._title = value

    @property
    def singer(self):
        return self._singer

    @singer.setter
    def singer(self, value):
        value = re.sub(r'[\\/:*?"<>|]', "", value)
        self._singer = value

    def _set_fullname(self):
        """ Full name without suffix, to resolve file name conflicts"""
        outdir = config.get("outdir")
        outfile = os.path.abspath(os.path.join(outdir, self.name))
        if os.path.exists(outfile):
            name, ext = self.name.rsplit(".", 1)
            names = [
                x for x in os.listdir(outdir) if x.startswith(name) and x.endswith(ext)
            ]
            names = [x.rsplit(".", 1)[0] for x in names]
            suffixes = [x.replace(name, "") for x in names]
            # filter suffixes that match ' (x)' pattern
            suffixes = [
                x[2:-1] for x in suffixes if x.startswith(" (") and x.endswith(")")
            ]
            indexes = [int(x) for x in suffixes if set(x) <= set("0123456789")]
            idx = 1
            if indexes:
                idx += sorted(indexes)[-1]
            self._fullname = os.path.abspath(
                os.path.join(outdir, "%s (%d)" % (name, idx))
            )
        else:
            self._fullname = outfile.rpartition(".")[0]

    @property
    def song_fullname(self):
        return self._fullname + "." + self.ext

    @property
    def lyrics_fullname(self):
        return self._fullname + ".lrc"

    @property
    def cover_fullname(self):
        return self._fullname + ".jpg"

    def _download_file(self, url, outfile, stream=False) -> str:
        """
            Helper function for download
        :param url:
        :param outfile:
        :param stream: need process bar or not
        :return:
        """
        if not url:
            print("URL is empty.")
            return ""
        try:
            r = requests.get(
                url,
                stream=stream,
                headers=config.get("wget_headers")
            )
            if not os.path.exists(outfile):
                if stream:
                    with open(outfile, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                else:
                    with open(outfile, "wb") as f:
                        f.write(r.content)
            return outfile
        except Exception as e:
            print("Download failed: " + "\n")
            print("URL: {url}".format(url=url) + "\n")
            print(
                "File location: {outfile}".format(outfile=outfile) + "\n"
            )
            print(str(e))

    def download_song(self) -> str:
        outfile = ""
        if self.song_url:
            outfile = self._download_file(self.song_url, self.song_fullname, stream=True)
        return outfile

    def _save_lyrics_text(self) -> str:
        with open(self.lyrics_fullname, "w", encoding="utf-8") as f:
            f.write(self.lyrics_text)
        return self.lyrics_fullname

    def download_lyrics(self):
        out_lyrics_file = ""
        if self.lyrics_url:
            out_lyrics_file = self._download_file(self.lyrics_url, self.lyrics_fullname, stream=False)
        return out_lyrics_file

    def download_cover(self):
        out_cover_file = ""
        if self.cover_url:
            out_cover_file = self._download_file(self.cover_url, self.cover_fullname, stream=False)
        return out_cover_file

    def download(self, song_flag=True, lyrics_flag=True, cover_flag=True) -> (str, str, str):
        """ Main download function """
        out_song_file = ""
        out_lyrics_file = ""
        out_cover_file = ""
        if song_flag:
            out_song_file = self.download_song()
        if lyrics_flag:
            out_lyrics_file = self.download_lyrics()
        if cover_flag:
            out_cover_file = self.download_cover()
        return out_song_file, out_lyrics_file, out_cover_file
