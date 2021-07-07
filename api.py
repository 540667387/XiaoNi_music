"""
@author: xuji0003
@file: api.py
@Description: TODO
@time: 2021/6/15
"""


import requests
import config
from exceptions import RequestError, ResponseError

class MusicApi:
    # class property
    # 子类修改时使用deepcopy
    session = requests.Session()
    session.headers.update(config.get("fake_headers"))
    session.headers.update({"referer": "http://www.google.com/"})

    @classmethod
    def request(cls, url, method="POST", data=None):
        if method == "GET":
            resp = cls.session.get(url, params=data, timeout=7)
        else:
            resp = cls.session.post(url, data=data, timeout=7)
        if resp.status_code != requests.codes.ok:
            raise RequestError(resp.text)
        if not resp.text:
            raise ResponseError("No response data.")
        return resp.json()